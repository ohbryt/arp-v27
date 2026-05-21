"""
ARP v27 - Core Module
Unified: v26 traceable OS + v25 self-healing + v22 schema
"""

__version__ = "27.0"

from .schema import TargetScores, DiseaseType
from .weights import DISEASE_WEIGHTS, MODALITY_PREFERENCES

__all__ = [
    "TargetScores",
    "DiseaseType",
    "DISEASE_WEIGHTS",
    "MODALITY_PREFERENCES",
]