"""
Skin Aging Ontology
Based on Li et al. EMBO Journal 2026
"""

SKIN_AGING_ONTOLOGY = {
    "name": "Skin Aging",
    "description": "Multi-layered mechanisms of skin aging across epidermis, dermis, and appendages",
    "categories": [
        {
            "name": "Epidermal Aging",
            "pathways": ["Stem cell exhaustion", "Keratinocyte senescence", "Barrier dysfunction"]
        },
        {
            "name": "Dermal Aging", 
            "pathways": ["Collagen degradation", "ECM remodeling", "Fibroblast senescence"]
        },
        {
            "name": "Appendage Aging",
            "pathways": ["Hair follicle stem cells", "Sebaceous glands", "Sweat glands"]
        },
        {
            "name": "Systemic Cross-talk",
            "pathways": ["Gut-skin axis", "Hormonal regulation", "Immune dysregulation"]
        }
    ],
    "key_phenotypes": [
        "Epidermal thinning",
        "Loss of rete ridges",
        "SASP accumulation",
        "ECM fragmentation",
        "Chronic inflammation",
        "Hair graying/loss",
        "Barrier dysfunction"
    ]
}
