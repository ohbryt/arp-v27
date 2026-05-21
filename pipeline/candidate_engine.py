"""
ARP v24 - Engine 3: Modality -> Candidate Generation

Fixed bugs:
1. Modality now explicit in COMPOUND_DATABASE (not inferred from SMILES)
2. Affinity-aware scoring (lower nM = better potency)
3. Score breakdown for explainability
"""

import time
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class CandidateCompound:
    """A candidate compound for a target"""
    compound_id: str
    name: str
    smiles: Optional[str] = None
    modality: str = "small_molecule"
    source: str = "literature"
    development_stage: str = "preclinical"
    target_name: str = ""
    binding_mode: str = "unknown"
    affinity: Optional[float] = None  # nM

    # ADMET scores (0-1)
    admet_score: float = 0.50
    absorption_score: float = 0.50
    distribution_score: float = 0.50
    metabolism_score: float = 0.50
    excretion_score: float = 0.50
    safety_score: float = 0.50

    # Developability
    solubility: float = 0.50
    permeability: float = 0.50
    metabolic_stability: float = 0.50
    herg_liability: float = 0.50

    # Efficacy
    efficacy_score: float = 0.50
    potency_score: float = 0.50
    modality_fit_score: float = 1.0

    # Composite
    composite_score: float = 0.0
    admet_composite: float = 0.0

    # Score breakdown for explainability
    intrinsic_score: float = 0.0
    affinity_potency_score: float = 0.0
    final_adjusted_score: float = 0.0

    # Metadata
    clinical_trials: List[str] = field(default_factory=list)
    approved_indications: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def _normalize_affinity_to_potency_score(self) -> float:
        """Convert affinity (nM) to potency score (0-1). Lower nM = better potency."""
        if self.affinity is None:
            return 0.50  # Default if no affinity
        if self.affinity <= 0:
            return 0.50
        # Log-scale normalization: 0.01 nM = 1.0, 10000 nM = 0.0
        log_nm = math.log10(self.affinity + 0.01)
        # Map log10(nM) to 0-1: log10(0.01)=-2 → 1.0, log10(10000)=4 → 0.0
        score = 1.0 - (log_nm + 2) / 6.0
        return max(0.0, min(1.0, score))

    def _compute_intrinsic_score(self) -> float:
        """Compute intrinsic compound score from ADMET and efficacy."""
        admet_c = (self.absorption_score * 0.20 + self.distribution_score * 0.15
                   + self.metabolism_score * 0.20 + self.excretion_score * 0.10
                   + self.safety_score * 0.35)
        self.admet_composite = (admet_c * 0.7 + self.admet_score * 0.3) if self.admet_score != 0.50 else admet_c

        dev = (self.solubility * 0.25 + self.permeability * 0.25
               + self.metabolic_stability * 0.25 + (1 - self.herg_liability) * 0.25)

        return (self.admet_composite * 0.35 + self.efficacy_score * 0.35
                + dev * 0.20 + self.potency_score * 0.10)

    def _compute_final_score(self) -> float:
        """Compute final adjusted score including modality fit and affinity."""
        # Step 1: Intrinsic score
        intrinsic = self._compute_intrinsic_score()
        self.intrinsic_score = intrinsic

        # Step 2: Affinity-aware potency score
        self.affinity_potency_score = self._normalize_affinity_to_potency_score()

        # Step 3: If we have real affinity data, blend it
        if self.affinity is not None and self.affinity > 0:
            adjusted_potency = self.affinity_potency_score
        else:
            adjusted_potency = self.potency_score

        # Step 4: Final composite with modality compatibility
        final = (intrinsic * 0.70 +
                 adjusted_potency * 0.20 * self.modality_fit_score +
                 self.potency_score * 0.10)

        # Apply modality fit as a modifier
        self.final_adjusted_score = final * self.modality_fit_score
        return self.final_adjusted_score

    def calculate_scores(self):
        """Compute all scores. Legacy method for backwards compatibility."""
        self._compute_intrinsic_score()
        self._compute_final_score()
        self.composite_score = self.final_adjusted_score

    def to_dict(self) -> Dict[str, Any]:
        self.calculate_scores()
        return {
            "compound_id": self.compound_id,
            "name": self.name,
            "smiles": self.smiles,
            "modality": self.modality,
            "source": self.source,
            "development_stage": self.development_stage,
            "target": self.target_name,
            "affinity_nM": self.affinity,
            "admet_score": round(self.admet_composite, 3),
            "efficacy_score": round(self.efficacy_score, 3),
            "composite_score": round(self.composite_score, 3),
            # Score breakdown for explainability
            "score_breakdown": {
                "intrinsic_score": round(self.intrinsic_score, 3),
                "affinity_potency_score": round(self.affinity_potency_score, 3),
                "modality_fit_score": round(self.modality_fit_score, 3),
                "final_adjusted_score": round(self.final_adjusted_score, 3),
            },
            "warnings": self.warnings,
        }


@dataclass
class CandidateRankingResult:
    target_id: str
    gene_name: str
    disease: str
    modality: str
    candidates: List[CandidateCompound]
    total_candidates: int
    ranking_time_seconds: float = 0.0

    def get_top_candidates(self, n: int = 10) -> List[CandidateCompound]:
        return sorted(self.candidates, key=lambda c: c.composite_score, reverse=True)[:n]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_id": self.target_id,
            "gene_name": self.gene_name,
            "disease": self.disease,
            "modality": self.modality,
            "total_candidates": self.total_candidates,
            "top_10": [
                {"name": c.name, "composite_score": round(c.composite_score, 3),
                 "admet_score": round(c.admet_composite, 3), "stage": c.development_stage}
                for c in self.get_top_candidates(10)
            ],
        }


# ============================================================================
# COMPOUND DATABASE - explicit modality for each compound
# ============================================================================

COMPOUND_DATABASE = {
    "masld": {
        "THRB": [
            {"name": "Resmetirom", "stage": "approved", "affinity": 0.21, "modality": "small_molecule"},
            {"name": "ASC-41", "stage": "phase2", "modality": "small_molecule"},
            {"name": "TERN-101", "stage": "phase2", "modality": "small_molecule"},
        ],
        "NR1H4": [
            {"name": "Obeticholic acid", "stage": "approved", "affinity": 90.0, "modality": "small_molecule"},
            {"name": "Cilofexor", "stage": "phase2", "modality": "small_molecule"},
            {"name": "Tropifexor", "stage": "phase2", "modality": "small_molecule"},
        ],
        "GLP1R": [
            {"name": "Semaglutide", "stage": "approved", "affinity": 0.015, "modality": "peptide"},
            {"name": "Liraglutide", "stage": "approved", "affinity": 0.038, "modality": "peptide"},
            {"name": "Tirzepatide", "stage": "approved", "affinity": 0.025, "modality": "peptide"},
        ],
        "SLC5A2": [
            {"name": "Empagliflozin", "stage": "approved", "affinity": 3.1, "modality": "small_molecule"},
            {"name": "Dapagliflozin", "stage": "approved", "affinity": 1.2, "modality": "small_molecule"},
        ],
    },
    "sarcopenia": {
        "MSTN": [
            {"name": "Bimagrumab", "stage": "phase2", "modality": "antibody"},
            {"name": "Apitegromab", "stage": "phase2", "modality": "antibody"},
            {"name": "Domagrozumab", "stage": "discontinued", "modality": "antibody"},
        ],
        "MTOR": [
            {"name": "Rapamycin", "stage": "approved", "affinity": 0.1, "modality": "small_molecule"},
            {"name": "Everolimus", "stage": "approved", "affinity": 0.3, "modality": "small_molecule"},
        ],
        "SIRT1": [
            {"name": "Resveratrol", "stage": "preclinical", "affinity": 100.0, "modality": "small_molecule"},
            {"name": "SRT2104", "stage": "phase1", "modality": "small_molecule"},
        ],
        "PRKAA1": [
            {"name": "Metformin", "stage": "approved", "affinity": 100.0, "modality": "small_molecule"},
            {"name": "AICAR", "stage": "preclinical", "modality": "small_molecule"},
        ],
    },
    "lung_fibrosis": {
        "TGFB1": [
            {"name": "Pirfenidone", "stage": "approved", "modality": "small_molecule"},
            {"name": "Nintedanib", "stage": "approved", "affinity": 80.0, "modality": "small_molecule"},
            {"name": "Pamrevlumab", "stage": "phase2", "modality": "antibody"},
        ],
    },
    "heart_failure": {
        "SLC5A2": [
            {"name": "Empagliflozin", "stage": "approved", "affinity": 3.1, "modality": "small_molecule"},
            {"name": "Dapagliflozin", "stage": "approved", "affinity": 1.2, "modality": "small_molecule"},
        ],
        "NPPA": [{"name": "Nesiritide", "stage": "approved", "affinity": 0.1, "modality": "peptide"}],
    },
    "cancer": {
        # ONCOLOGY KINASE INHIBITORS - all small_molecule (NOT biologic!)
        "EGFR": [
            {"name": "Osimertinib", "stage": "approved", "affinity": 0.7, "modality": "small_molecule"},
            {"name": "Erlotinib", "stage": "approved", "affinity": 2.0, "modality": "small_molecule"},
            {"name": "Gefitinib", "stage": "approved", "affinity": 1.0, "modality": "small_molecule"},
            {"name": "Afatinib", "stage": "approved", "affinity": 0.5, "modality": "small_molecule"},
        ],
        "ALK": [
            {"name": "Alectinib", "stage": "approved", "affinity": 1.9, "modality": "small_molecule"},
            {"name": "Lorlatinib", "stage": "approved", "affinity": 0.7, "modality": "small_molecule"},
        ],
        "MET": [
            {"name": "Capmatinib", "stage": "approved", "affinity": 0.6, "modality": "small_molecule"},
            {"name": "Tepotinib", "stage": "approved", "affinity": 3.0, "modality": "small_molecule"},
        ],
        "KRAS": [
            {"name": "Sotorasib", "stage": "approved", "affinity": 10.0, "modality": "small_molecule"},
            {"name": "Adagrasib", "stage": "approved", "affinity": 5.0, "modality": "small_molecule"},
        ],
        # IMMUNE CHECKPOINT - antibodies (biologic)
        "CD274": [
            {"name": "Pembrolizumab", "stage": "approved", "affinity": 0.1, "modality": "antibody"},
            {"name": "Atezolizumab", "stage": "approved", "affinity": 0.1, "modality": "antibody"},
        ],
    },
}

# Stage -> base ADMET/efficacy scores
STAGE_SCORES = {
    "approved": dict(admet_score=0.85, absorption_score=0.85, distribution_score=0.80,
                     metabolism_score=0.80, excretion_score=0.82, safety_score=0.80,
                     solubility=0.82, permeability=0.80, metabolic_stability=0.82,
                     herg_liability=0.15, efficacy_score=0.85, potency_score=0.85),
    "phase3": dict(admet_score=0.78, absorption_score=0.80, distribution_score=0.75,
                   metabolism_score=0.75, excretion_score=0.78, safety_score=0.75,
                   solubility=0.78, permeability=0.75, metabolic_stability=0.75,
                   herg_liability=0.20, efficacy_score=0.80, potency_score=0.80),
    "phase2": dict(admet_score=0.70, absorption_score=0.72, distribution_score=0.68,
                   metabolism_score=0.68, excretion_score=0.70, safety_score=0.68,
                   solubility=0.70, permeability=0.70, metabolic_stability=0.68,
                   herg_liability=0.25, efficacy_score=0.72, potency_score=0.75),
    "phase1": dict(admet_score=0.65, absorption_score=0.68, distribution_score=0.62,
                   metabolism_score=0.62, excretion_score=0.65, safety_score=0.60,
                   solubility=0.65, permeability=0.65, metabolic_stability=0.60,
                   herg_liability=0.30, efficacy_score=0.60, potency_score=0.70),
    "preclinical": dict(admet_score=0.55, absorption_score=0.58, distribution_score=0.52,
                        metabolism_score=0.52, excretion_score=0.55, safety_score=0.50,
                        solubility=0.55, permeability=0.55, metabolic_stability=0.50,
                        herg_liability=0.35, efficacy_score=0.50, potency_score=0.60),
    "discontinued": dict(admet_score=0.30, absorption_score=0.35, distribution_score=0.30,
                         metabolism_score=0.30, excretion_score=0.32, safety_score=0.25,
                         solubility=0.35, permeability=0.32, metabolic_stability=0.30,
                         herg_liability=0.50, efficacy_score=0.30, potency_score=0.40),
}

# Modality compatibility matrix
MODALITY_COMPAT = {
    ("small_molecule", "biologic"): 0.3,
    ("small_molecule", "peptide"): 0.6,
    ("small_molecule", "antibody"): 0.2,
    ("small_molecule", "degrader"): 0.7,
    ("biologic", "small_molecule"): 0.3,
    ("biologic", "antibody"): 0.9,
    ("biologic", "peptide"): 0.8,
    ("peptide", "small_molecule"): 0.4,
    ("peptide", "biologic"): 0.7,
    ("antibody", "biologic"): 0.9,
    # Same modality = perfect fit
    ("small_molecule", "small_molecule"): 1.0,
    ("biologic", "biologic"): 1.0,
    ("antibody", "antibody"): 1.0,
    ("peptide", "peptide"): 1.0,
}


class CandidateEngine:
    """Engine 3: Retrieves/ranks candidate compounds for targets."""

    def __init__(self):
        self.db = COMPOUND_DATABASE

    def generate_candidates(
        self, gene_name: str, disease: str,
        modality: str = "small_molecule",
    ) -> CandidateRankingResult:
        start = time.time()
        candidates = []
        target_compounds = self.db.get(disease, {}).get(gene_name, [])

        for i, data in enumerate(target_compounds):
            c = self._create_candidate(f"{gene_name}_{i+1}", gene_name, modality, **data)
            candidates.append(c)

        for c in candidates:
            c.calculate_scores()

        candidates.sort(key=lambda x: x.composite_score, reverse=True)

        return CandidateRankingResult(
            f"{gene_name}_{disease}", gene_name, disease, modality,
            candidates, len(candidates), time.time() - start,
        )

    def _create_candidate(
        self, cid: str, gene: str, modality_hint: str,
        name: str, stage: str = "preclinical",
        affinity: float = None, smiles: str = None,
        modality: str = None,  # EXPLICIT modality parameter
    ) -> CandidateCompound:
        scores = STAGE_SCORES.get(stage, STAGE_SCORES["preclinical"])
        
        # Use explicit modality if provided, otherwise fall back to old logic
        if modality is not None:
            actual_mod = modality
        elif smiles:
            actual_mod = "small_molecule"
        else:
            actual_mod = "biologic"
        
        fit = MODALITY_COMPAT.get((actual_mod, modality_hint), 0.5)
        
        # Add warning if modality mismatch
        warnings = []
        if actual_mod != modality_hint and actual_mod == "biologic":
            warnings.append(f"Modality mismatch: compound is {actual_mod}, requested {modality_hint}")

        return CandidateCompound(
            compound_id=cid, name=name, smiles=smiles,
            modality=actual_mod, source="literature",
            development_stage=stage, target_name=gene,
            affinity=affinity, modality_fit_score=fit,
            warnings=warnings, **scores,
        )
