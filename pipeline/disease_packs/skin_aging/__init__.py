"""
ARP v27 - Skin Aging Disease Pack
Based on: Li et al. (2026) "Skin aging: mechanisms, evaluation, and rejuvenation"
EMBO Journal, https://doi.org/10.1038/s44318-026-00810-3

Key Targets:
- COL17A1: HFSC anchoring, proteolysis drives depletion
- TERT: Telomerase reactivation reverses degeneration
- Wnt/β-catenin: Androgen antagonizes this pathway
- SASP factors: MMPs, IL-1α, IL-6, TNF-α
- Setdb1: Epigenetic ERV silencing
"""

from .targets import SKIN_AGING_TARGETS, SKIN_AGING_PRIORITY_TARGETS

__all__ = ['SKIN_AGING_TARGETS', 'SKIN_AGING_PRIORITY_TARGETS']