"""
ARP v24 - Engine 2: Target -> Modality Routing

Ported from v22. Scores modality options and recommends best fit.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

from .schema import DiseaseType, TargetDossier
from .weights import MODALITY_PREFERENCES, Disease


@dataclass
class ModalityScore:
    modality: str
    score: float
    fit_score: float
    disease_score: float
    safety_score: float
    developability_score: float
    timeline_years: float
    estimated_cost: str
    rationale: str
    key_advantages: List[str] = field(default_factory=list)
    key_risks: List[str] = field(default_factory=list)
    recommended: bool = False


@dataclass
class ModalityRoutingResult:
    target_id: str
    gene_name: str
    disease: str
    recommended_modalities: List[ModalityScore]
    primary_recommendation: Optional[ModalityScore] = None
    routing_time_seconds: float = 0.0

    def get_top_modality(self) -> Optional[str]:
        return self.recommended_modalities[0].modality if self.recommended_modalities else None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_id": self.target_id, "gene_name": self.gene_name,
            "disease": self.disease, "primary_modality": self.get_top_modality(),
            "all_modalities": [
                {"modality": m.modality, "score": round(m.score, 3),
                 "recommended": m.recommended, "timeline": m.timeline_years}
                for m in self.recommended_modalities
            ],
        }


@dataclass
class AssayRecommendation:
    assay_name: str
    assay_type: str
    readout: str
    priority: str
    gold_standard: bool = False
    estimated_cost: str = "moderate"
    timeline_weeks: int = 4


class ModalityRouter:
    """Engine 2: Routes targets to appropriate modalities."""

    TARGET_CLASS_DEFAULTS = {
        "kinase": {"small_molecule": 0.90, "degrader": 0.70, "biologic": 0.40},
        "nuclear_receptor": {"small_molecule": 0.95, "peptide": 0.25},
        "gpcr": {"small_molecule": 0.80, "peptide": 0.90, "biologic": 0.70},
        "transporter": {"small_molecule": 0.95},
        "enzyme": {"small_molecule": 0.85, "oligo": 0.65, "biologic": 0.50},
        "transcription_factor": {"oligo": 0.80, "degrader": 0.75, "small_molecule": 0.35},
        "extracellular_ligand": {"biologic": 0.95, "peptide": 0.80, "antibody": 0.90, "small_molecule": 0.40},
        "ion_channel": {"small_molecule": 0.95},
        "cell_surface_antigen": {"antibody": 0.95, "adc": 0.90, "biologic": 0.80},
    }

    TIMELINE_COST = {
        "small_molecule": (5.0, "moderate"), "biologic": (6.0, "high"),
        "peptide": (5.5, "moderate"), "oligo": (6.5, "high"),
        "antibody": (5.5, "high"), "adc": (7.0, "very_high"),
        "degrader": (6.0, "high"), "inhaled_small_molecule": (5.5, "moderate"),
    }

    SAFETY_CHRONIC = {
        "small_molecule": 0.70, "biologic": 0.85, "peptide": 0.80,
        "oligo": 0.75, "antibody": 0.85, "adc": 0.60, "degrader": 0.65,
    }

    PROS_CONS = {
        "small_molecule": (["Oral possible", "Established path", "Good tissue penetration"],
                           ["Off-target risk", "Metabolic stability", "Selectivity"]),
        "biologic": (["High specificity", "Lower off-target", "Proven safety"],
                     ["Injection only", "High cost", "Immunogenicity"]),
        "peptide": (["High specificity", "PPI modulation", "Better penetration than Ab"],
                    ["Stability", "Delivery", "Short half-life"]),
        "antibody": (["Very high specificity", "Long half-life", "Proven success"],
                     ["Injection only", "High cost", "No intracellular targets"]),
        "degrader": (["Protein degradation", "Overcome resistance", "Catalytic"],
                     ["Chemistry challenge", "PK/PD optimization", "Novel regulatory"]),
        "oligo": (["Undruggable targets", "High specificity", "GalNAc liver targeting"],
                  ["Delivery", "Stability", "Manufacturing cost"]),
    }

    def route_target(self, target: TargetDossier, disease: DiseaseType) -> ModalityRoutingResult:
        start = time.time()
        disease_enum = Disease(disease.value)
        disease_prefs = MODALITY_PREFERENCES.get(disease_enum, {})
        tc = target.target_class.value if target.target_class else "enzyme"
        class_scores = self.TARGET_CLASS_DEFAULTS.get(tc, {"small_molecule": 0.70})

        all_modalities = set(list(class_scores.keys()) + list(disease_prefs.keys()))
        results = []

        for mod in all_modalities:
            fit = class_scores.get(mod, 0.30)
            ds = disease_prefs.get(mod, 0.50)
            safety = self.SAFETY_CHRONIC.get(mod, 0.60)
            dev = self._calc_dev(mod, target)
            composite = fit * 0.35 + ds * 0.25 + safety * 0.20 + dev * 0.20
            timeline, cost = self.TIMELINE_COST.get(mod, (6.0, "moderate"))
            pros, cons = self.PROS_CONS.get(mod, (["Viable"], ["Challenges"]))

            fit_txt = "excellent" if fit >= 0.80 else "good" if fit >= 0.60 else "moderate"
            results.append(ModalityScore(
                mod, composite, fit, ds, safety, dev, timeline, cost,
                f"{fit_txt} target fit", pros, cons,
            ))

        results.sort(key=lambda x: x.score, reverse=True)
        if results:
            results[0].recommended = True

        return ModalityRoutingResult(
            target.target_id, target.gene_name, disease.value,
            results, results[0] if results else None, time.time() - start,
        )

    def _calc_dev(self, mod: str, target: TargetDossier) -> float:
        base = {"small_molecule": 0.85, "biologic": 0.70, "peptide": 0.75,
                "oligo": 0.60, "antibody": 0.70, "adc": 0.50, "degrader": 0.55}.get(mod, 0.50)
        if target.is_extracellular and mod in ("biologic", "antibody", "peptide"):
            base += 0.10
        if target.is_liver_specific and mod in ("oligo", "liver_targeted_oligo"):
            base += 0.15
        return min(1.0, base)


class AssayEngine:
    """Generates assay recommendations per disease."""

    TEMPLATES = {
        "masld": [
            AssayRecommendation("Hepatocyte lipid accumulation", "In vitro", "Nile red fluorescence", "primary", True),
            AssayRecommendation("Stellate cell activation", "In vitro", "a-SMA qPCR", "primary", True),
            AssayRecommendation("Inflammatory cytokine panel", "Multiplex", "IL-6/TNF-a/IL-1b", "secondary"),
        ],
        "sarcopenia": [
            AssayRecommendation("Myotube atrophy rescue", "In vitro", "Myotube diameter", "primary", True),
            AssayRecommendation("Muscle protein synthesis", "Metabolic", "3H-leucine incorporation", "primary", True),
            AssayRecommendation("Mitochondrial function", "Seahorse XF", "OCR/ECAR", "secondary"),
        ],
        "lung_fibrosis": [
            AssayRecommendation("Fibroblast activation", "In vitro", "a-SMA, contraction", "primary", True),
            AssayRecommendation("Collagen deposition", "Biochemical", "Hydroxyproline", "primary", True),
        ],
        "heart_failure": [
            AssayRecommendation("Cardiomyocyte hypertrophy", "In vitro", "Cell size, ANP/BNP", "primary", True),
            AssayRecommendation("Contractility", "iPSC-CMs", "Beating rate", "primary", True),
        ],
        "cancer": [
            AssayRecommendation("Cell viability", "Cell line", "CellTiter-Glo", "primary", True),
            AssayRecommendation("CRISPR dependency", "Genome-wide", "Dependency score", "primary", True),
        ],
    }

    def get_assays(self, disease: DiseaseType, target_class: Optional[str] = None) -> List[AssayRecommendation]:
        return self.TEMPLATES.get(disease.value, [])
