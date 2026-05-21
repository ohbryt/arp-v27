"""
ARP v24 - Engine 1: Disease -> Target Scoring

Ported from v22 with all bugs fixed. Scores candidate targets using
disease-specific weight matrices and returns prioritized dossiers.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from datetime import date

from .schema import (
    TargetDossier, TargetScores, TargetPrioritizationResult,
    DiseaseContextData, Penalty, DiseaseType, TargetClass, Status,
    ScoringEngineConfig,
)
from .weights import (
    get_disease_weights, get_penalties_for_disease,
    MODALITY_PREFERENCES, TARGET_CLASS_MODALITY, Disease,
)


@dataclass
class TargetInfo:
    """Known information about a target"""
    gene_name: str
    protein_name: str
    target_class: TargetClass
    is_extracellular: bool
    is_liver_specific: bool
    has_known_pocket: bool
    has_degradation_logic: bool
    default_scores: Optional[TargetScores] = None
    default_penalties: List[str] = field(default_factory=list)


# Pre-populated target registry (30+ targets across 5 diseases)
TARGET_REGISTRY: Dict[str, Dict[str, TargetInfo]] = {
    "masld": {
        "THRB": TargetInfo("THRB", "Thyroid hormone receptor beta", TargetClass.NUCLEAR_RECEPTOR, False, False, True, False),
        "NR1H4": TargetInfo("NR1H4", "Farnesoid X receptor (FXR)", TargetClass.NUCLEAR_RECEPTOR, False, True, True, False),
        "PPARA": TargetInfo("PPARA", "PPARalpha", TargetClass.NUCLEAR_RECEPTOR, False, True, True, False),
        "GLP1R": TargetInfo("GLP1R", "GLP-1 receptor", TargetClass.GPCR, True, False, True, False),
        "SLC5A2": TargetInfo("SLC5A2", "SGLT2", TargetClass.TRANSPORTER, True, False, True, False),
        "NLRP3": TargetInfo("NLRP3", "NLRP3 inflammasome", TargetClass.ENZYME, False, False, True, False),
        "ACACA": TargetInfo("ACACA", "Acetyl-CoA carboxylase", TargetClass.ENZYME, False, True, True, False),
        "SREBF1": TargetInfo("SREBF1", "SREBP-1", TargetClass.TRANSCRIPTION_FACTOR, False, True, False, True),
    },
    "sarcopenia": {
        "MTOR": TargetInfo("MTOR", "mTOR kinase", TargetClass.KINASE, False, False, True, False, default_penalties=["immunosuppression", "tumor_growth_concern"]),
        "FOXO1": TargetInfo("FOXO1", "FOXO1", TargetClass.TRANSCRIPTION_FACTOR, False, False, False, True),
        "FOXO3": TargetInfo("FOXO3", "FOXO3", TargetClass.TRANSCRIPTION_FACTOR, False, False, False, True),
        "PRKAA1": TargetInfo("PRKAA1", "AMPK alpha-1", TargetClass.KINASE, False, False, True, False),
        "MSTN": TargetInfo("MSTN", "Myostatin", TargetClass.EXTRACELLULAR_LIGAND, True, False, True, False),
        "AKT1": TargetInfo("AKT1", "AKT1 kinase", TargetClass.KINASE, False, False, True, False, default_penalties=["tumor_growth_concern"]),
        "MYOD1": TargetInfo("MYOD1", "MyoD", TargetClass.TRANSCRIPTION_FACTOR, False, False, False, False),
        "PPARGC1A": TargetInfo("PPARGC1A", "PGC-1alpha", TargetClass.TRANSCRIPTION_FACTOR, False, False, False, False),
        "SIRT1": TargetInfo("SIRT1", "Sirtuin 1", TargetClass.ENZYME, False, False, True, False),
    },
    "lung_fibrosis": {
        "TGFB1": TargetInfo("TGFB1", "TGF-beta 1", TargetClass.EXTRACELLULAR_LIGAND, True, False, True, False, default_penalties=["wound_healing_inhibition", "epithelial_regeneration_impairment"]),
        "COL1A1": TargetInfo("COL1A1", "Collagen I alpha 1", TargetClass.EXTRACELLULAR_LIGAND, True, False, False, False),
        "MMP7": TargetInfo("MMP7", "MMP-7", TargetClass.ENZYME, True, False, True, False),
        "ITGAV": TargetInfo("ITGAV", "Integrin alpha-V", TargetClass.CELL_SURFACE_ANTIGEN, True, False, True, False),
        "CTGF": TargetInfo("CTGF", "CTGF", TargetClass.EXTRACELLULAR_LIGAND, True, False, True, False),
    },
    "heart_failure": {
        "NPPA": TargetInfo("NPPA", "ANP", TargetClass.EXTRACELLULAR_LIGAND, True, False, True, False),
        "NPPB": TargetInfo("NPPB", "BNP", TargetClass.EXTRACELLULAR_LIGAND, True, False, True, False),
        "SLC5A2": TargetInfo("SLC5A2", "SGLT2", TargetClass.TRANSPORTER, True, False, True, False),
        "EDNRA": TargetInfo("EDNRA", "ET-A receptor", TargetClass.GPCR, True, False, True, False, default_penalties=["qtc_herg_risk", "pro_arrhythmia"]),
        "NFKB1": TargetInfo("NFKB1", "NF-kB", TargetClass.TRANSCRIPTION_FACTOR, False, False, False, True),
    },
    "cancer": {
        "EGFR": TargetInfo("EGFR", "EGFR", TargetClass.KINASE, False, False, True, False),
        "ALK": TargetInfo("ALK", "ALK", TargetClass.KINASE, False, False, True, False),
        "MET": TargetInfo("MET", "MET", TargetClass.KINASE, False, False, True, False),
        "KRAS": TargetInfo("KRAS", "KRAS G12C", TargetClass.KINASE, False, False, True, False),
        "CD274": TargetInfo("CD274", "PD-L1", TargetClass.CELL_SURFACE_ANTIGEN, True, False, True, False),
        "PARP1": TargetInfo("PARP1", "PARP1", TargetClass.ENZYME, False, False, True, False),
    },
}


DISEASE_CONTEXTS: Dict[DiseaseType, DiseaseContextData] = {
    DiseaseType.MASLD: DiseaseContextData(
        DiseaseType.MASLD, "MASH with fibrosis", "F2-F3", "fibrosis",
        ["steatosis", "inflammation"], ["hepatocyte", "hepatic_stellate", "kupffer_cell"],
        "Adults with biopsy-proven MASH",
    ),
    DiseaseType.SARCOPENIA: DiseaseContextData(
        DiseaseType.SARCOPENIA, "Age-related", "Moderate to severe", "muscle_function",
        ["anabolism", "catabolism", "mitochondrial"], ["skeletal_muscle", "satellite_cell"],
        "Older adults >= 65 years",
    ),
    DiseaseType.LUNG_FIBROSIS: DiseaseContextData(
        DiseaseType.LUNG_FIBROSIS, "IPF", "Mild to moderate", "fibrosis",
        ["epithelial_dysfunction", "inflammation"], ["lung_fibroblast", "alveolar_epithelium"],
        "Adults with IPF",
    ),
    DiseaseType.HEART_FAILURE: DiseaseContextData(
        DiseaseType.HEART_FAILURE, "HFrEF", "NYHA II-III", "remodeling",
        ["fibrosis", "contractility", "metabolism"], ["cardiomyocyte", "cardiac_fibroblast"],
        "Adults with HFrEF EF<40%",
    ),
    DiseaseType.CANCER: DiseaseContextData(
        DiseaseType.CANCER, "NSCLC EGFR-mutant", "Advanced", "oncogenic_dependency",
        ["resistance", "immune_evasion"], ["tumor_cell"],
        "Adults with EGFRm NSCLC",
    ),
}


class TargetScorer:
    """Engine 1: Scores targets using disease-specific weight matrices."""

    def __init__(self, config: Optional[ScoringEngineConfig] = None):
        self.config = config or ScoringEngineConfig()

    def score_target(
        self, target_info: TargetInfo, disease: DiseaseType,
        disease_context: Optional[DiseaseContextData] = None,
        score_overrides: Optional[Dict[str, float]] = None,
    ) -> Tuple[TargetScores, List[Penalty], float]:
        disease_enum = Disease(disease.value)
        weights = get_disease_weights(disease_enum)

        if score_overrides:
            base = target_info.default_scores or self._generate_default_scores(target_info, disease)
            d = base.to_dict()
            d.update(score_overrides)
            scores = TargetScores(**d)
        elif target_info.default_scores:
            scores = target_info.default_scores
        else:
            scores = self._generate_default_scores(target_info, disease)

        priority_score = self._calculate_priority_score(scores, weights)
        penalties = self._apply_penalties(target_info, disease, scores)
        if penalties:
            penalty_reduction = sum(p.severity for p in penalties) / len(penalties)
            priority_score *= (1 - penalty_reduction * 0.3)

        return scores, penalties, priority_score

    def _generate_default_scores(self, target_info: TargetInfo, disease: DiseaseType) -> TargetScores:
        base = {
            DiseaseType.MASLD: TargetScores(0.45, 0.50, 0.50, 0.60 if target_info.is_liver_specific else 0.40, 0.60, 0.50, 0.45, 0.50),
            DiseaseType.SARCOPENIA: TargetScores(0.45, 0.50, 0.50, 0.40, 0.55, 0.50, 0.45, 0.50),
            DiseaseType.LUNG_FIBROSIS: TargetScores(0.40, 0.50, 0.50, 0.55, 0.55, 0.50, 0.50, 0.50),
            DiseaseType.HEART_FAILURE: TargetScores(0.50, 0.50, 0.50, 0.50, 0.60, 0.45, 0.55, 0.50),
            DiseaseType.CANCER: TargetScores(0.55, 0.50, 0.50, 0.35, 0.60, 0.40, 0.50, 0.55),
        }
        return base.get(disease, TargetScores(0.40, 0.40, 0.40, 0.40, 0.50, 0.40, 0.40, 0.50))

    def _calculate_priority_score(self, scores: TargetScores, weights: Any) -> float:
        return (
            scores.genetic_causality * weights.genetic_causality
            + scores.disease_context * weights.disease_context
            + scores.perturbation_rescue * weights.perturbation_rescue
            + scores.tissue_specificity * weights.tissue_specificity
            + scores.druggability * weights.druggability
            + scores.safety * weights.safety
            + scores.translation * weights.translation
            + scores.competitive_novelty * weights.competitive_novelty
        )

    def _apply_penalties(self, target_info: TargetInfo, disease: DiseaseType, scores: TargetScores) -> List[Penalty]:
        penalties = []
        disease_enum = Disease(disease.value)
        penalty_configs = get_penalties_for_disease(disease_enum)

        for penalty_name in target_info.default_penalties:
            for config in penalty_configs:
                if config.name == penalty_name:
                    penalties.append(Penalty(
                        config.name, config.default_severity,
                        f"Known liability for {target_info.gene_name}",
                        "Class-based or known liability",
                    ))
        if scores.safety < 0.5:
            for config in penalty_configs:
                if "safety" in config.name.lower():
                    penalties.append(Penalty(
                        config.name, config.default_severity * (1 - scores.safety),
                        "Low safety score", "Safety dimension",
                    ))
        return penalties


class DiseaseEngine:
    """Main engine for disease-to-target prioritization."""

    def __init__(self, config: Optional[ScoringEngineConfig] = None):
        self.scorer = TargetScorer(config)
        self.config = config or ScoringEngineConfig()

    def prioritize_targets(
        self, disease: DiseaseType,
        candidate_genes: Optional[List[str]] = None,
        disease_context: Optional[DiseaseContextData] = None,
        score_overrides: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> TargetPrioritizationResult:
        start_time = time.time()
        ctx = disease_context or DISEASE_CONTEXTS.get(disease)

        if candidate_genes is None:
            candidate_genes = list(TARGET_REGISTRY.get(disease.value, {}).keys())

        dossiers = []
        for gene in candidate_genes:
            target_info = TARGET_REGISTRY.get(disease.value, {}).get(gene)
            if target_info is None:
                target_info = TargetInfo(gene, gene, TargetClass.ENZYME, False, False, True, False)

            gene_overrides = score_overrides.get(gene) if score_overrides else None
            scores, penalties, priority_score = self.scorer.score_target(
                target_info, disease, ctx, gene_overrides,
            )

            confidence = self._calculate_confidence(scores, penalties)
            modalities = self._get_recommended_modalities(target_info, disease, priority_score)

            dossier = TargetDossier(
                target_id=f"{gene}_{disease.value}", gene_name=gene,
                protein_name=target_info.protein_name, disease=disease,
                disease_context=ctx, scores=scores, penalties=penalties,
                priority_score=priority_score, confidence=confidence,
                recommended_modalities=modalities,
                target_class=target_info.target_class,
                is_extracellular=target_info.is_extracellular,
                is_liver_specific=target_info.is_liver_specific,
                has_known_pocket=target_info.has_known_pocket,
                has_degradation_logic=target_info.has_degradation_logic,
                status=Status.PRIORITIZED if priority_score >= self.config.min_priority_score else Status.DEPRIORITIZED,
                created_date=date.today(), last_updated=date.today(),
            )
            dossiers.append(dossier)

        dossiers.sort(key=lambda d: d.priority_score, reverse=True)
        for i, d in enumerate(dossiers):
            d.rank = i + 1

        quality_gate = len(dossiers) >= 5 and any(d.priority_score >= 0.70 for d in dossiers)
        elapsed = time.time() - start_time

        return TargetPrioritizationResult(
            disease=disease, targets=dossiers[:self.config.max_targets_returned],
            total_candidates_evaluated=len(candidate_genes),
            scoring_time_seconds=elapsed, quality_gate_passed=quality_gate,
        )

    def _calculate_confidence(self, scores: TargetScores, penalties: List[Penalty]) -> float:
        vals = [scores.genetic_causality, scores.disease_context, scores.perturbation_rescue,
                scores.tissue_specificity, scores.druggability, scores.safety,
                scores.translation, scores.competitive_novelty]
        mean = sum(vals) / len(vals)
        variance = sum((s - mean) ** 2 for s in vals) / len(vals)
        conf = 1 - min(variance * 2, 0.5)
        penalty_red = sum(p.severity for p in penalties) / max(len(penalties), 1) * 0.2
        return max(0.3, min(0.95, conf - penalty_red))

    def _get_recommended_modalities(self, target_info: TargetInfo, disease: DiseaseType, priority_score: float) -> List[str]:
        class_key = target_info.target_class.value
        class_prefs = TARGET_CLASS_MODALITY.get(class_key, {})
        disease_enum = Disease(disease.value)
        disease_prefs = MODALITY_PREFERENCES.get(disease_enum, {})

        combined = {}
        for modality, class_score in class_prefs.items():
            disease_score = disease_prefs.get(modality, 0.5)
            combined[modality] = class_score * 0.6 + disease_score * 0.4

        sorted_m = sorted(combined.items(), key=lambda x: x[1], reverse=True)
        threshold = 0.4 if priority_score >= 0.80 else 0.5
        limit = 4 if priority_score >= 0.80 else 3
        return [m for m, s in sorted_m if s > threshold][:limit]
