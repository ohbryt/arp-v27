"""
Skin Aging Target Definitions
Based on Li et al. EMBO Journal 2026

Key Pathways:
- Epidermal stem cell exhaustion
- COL17A1/HFSC anchoring
- SASP (Senescence-Associated Secretory Phenotype)
- Gut-skin axis (LPS/TLR4/NF-κB)
- Hormonal regulation (estrogen, GH/IGF-1, androgens)
- Telomere attrition
- Epigenetic drift (Setdb1/ERV silencing)
"""

SKIN_AGING_TARGETS = {
    'COL17A1': {
        'gene_name': 'Collagen Type XVII Alpha 1 Chain',
        'uniprot_id': 'Q9UMD9',
        'priority': 1,
        'target_class': 'Structural Protein',
        'pathway': 'Hemidesmosome/HFSC Anchoring',
        'description': 'COL17A1 is critical for epidermal stem cell anchoring to basement membrane. Age-associated proteolysis of COL17A1 weakens HFSC anchoring, promoting aberrant upward differentiation and stem cell pool depletion.',
        'rationale': 'COL17A1 proteolysis is a root cause of HFSC exhaustion. Restoring COL17A1 or inhibiting its proteolysis could regenerate functional HFSCs. Mouse studies show COL17A1 re-expression reverses aging phenotypes.',
        'genetic_evidence': 'COL17A1 knockout causes stem cell depletion and skin atrophy',
        'drug_modality': ['Small molecule stabilizer', 'Gene therapy', 'Protein replacement'],
        'development_stage': 'Research',
        'novelty_score': 9.0,
        'druggability_score': 7.5,
        'safety_score': 8.0,
        'priority_score': 8.5,
        'known_inhibitors': [
            {'name': 'COL17A1 gene therapy', 'type': 'Gene therapy', 'status': 'Preclinical'},
        ],
        'screening_assay': 'HFSC adhesion assay, COL17A1 protein levels',
        'validation_model': 'Aged mouse skin, 3D skin organoids'
    },
    'TERT': {
        'gene_name': 'Telomerase Reverse Transcriptase',
        'uniprot_id': 'O14746',
        'priority': 2,
        'target_class': 'Enzyme',
        'pathway': 'Telomere Maintenance',
        'description': 'TERT maintains telomere length in stem cells. Late-generation mTR-/- mice develop profound hair/skin degeneration. Telomerase reactivation can partially reverse degenerative changes.',
        'rationale': 'Telomere attrition is a key driver of skin aging. TERT activation promotes progenitor activity and telogen-to-anagen transition. However, must be carefully controlled to avoid cancer risk.',
        'genetic_evidence': 'TERT gain-of-function promotes progenitor activity and hair regeneration',
        'drug_modality': ['Small molecule activator', 'Gene therapy'],
        'development_stage': 'Research (cancer risk concerns)',
        'novelty_score': 8.0,
        'druggability_score': 6.5,
        'safety_score': 6.0,
        'priority_score': 7.0,
        'known_inhibitors': [
            {'name': 'TERT activator compounds', 'type': 'Small molecule', 'status': 'Research'},
        ],
        'screening_assay': 'Telomere length assay, telomerase activity',
        'validation_model': 'mTR-/- mice, aged human skin xenografts'
    },
    'MMP1': {
        'gene_name': 'Matrix Metalloproteinase 1',
        'uniprot_id': 'P03956',
        'priority': 3,
        'target_class': 'Protease',
        'pathway': 'ECM Degradation/SASP',
        'description': 'MMP1 degrades collagen and ECM components. SASP factors from senescent cells (keratinocytes, fibroblasts) secrete MMP1, driving skin thinning and wrinkle formation.',
        'rationale': 'MMP1 is downstream of SASP and NF-κB signaling. Inhibiting MMP1 could prevent ECM degradation. Broad MMP inhibition has side effects; need selective targeting.',
        'genetic_evidence': 'UV-induced MMP1 drives photoaging phenotype',
        'drug_modality': ['Selective MMP inhibitor', 'SASP inhibitor', 'Senolytic'],
        'development_stage': 'Research',
        'novelty_score': 7.0,
        'druggability_score': 8.5,
        'safety_score': 7.5,
        'priority_score': 7.5,
        'known_inhibitors': [
            {'name': 'GM6001 (broad MMP inhibitor)', 'type': 'MMP inhibitor', 'status': 'Research'},
            {'name': 'Topical MMP inhibitors', 'type': 'Topical', 'status': 'Cosmecuticals'},
        ],
        'screening_assay': 'MMP1 activity assay, collagen degradation',
        'validation_model': 'UV-exposed mouse skin, aged fibroblasts'
    },
    'IL6': {
        'gene_name': 'Interleukin 6',
        'uniprot_id': 'P05231',
        'priority': 4,
        'target_class': 'Cytokine',
        'pathway': 'SASP/Inflammation',
        'description': 'IL-6 is a key SASP factor secreted by senescent keratinocytes and fibroblasts. Drives chronic inflammation, MMP production, and impairs stem cell function.',
        'rationale': 'IL-6 is upstream of multiple aging pathways. Anti-IL-6 antibodies (tocilizumab) are approved for inflammatory diseases. Topical or local delivery could avoid systemic effects.',
        'genetic_evidence': 'IL-6 overexpression causes skin inflammation and aging phenotypes',
        'drug_modality': ['Anti-IL-6 antibody', 'Small molecule inhibitor', 'JAK inhibitor'],
        'development_stage': 'Clinical (inflammatory diseases)',
        'novelty_score': 7.5,
        'druggability_score': 9.0,
        'safety_score': 8.0,
        'priority_score': 8.0,
        'known_inhibitors': [
            {'name': 'Tocilizumab (anti-IL-6R)', 'type': 'mAb', 'status': 'Approved (RA)'},
            {'name': 'Sarilumab (anti-IL-6R)', 'type': 'mAb', 'status': 'Approved (RA)'},
            {'name': 'JAK inhibitors (ruxolitinib)', 'type': 'JAK inhibitor', 'status': 'Approved (myelofibrosis)'},
        ],
        'screening_assay': 'IL-6 secretion assay, p-STAT3 signaling',
        'validation_model': 'Senescent cell coculture, aged mouse skin'
    },
    'TP53': {
        'gene_name': 'Tumor Protein p53',
        'uniprot_id': 'P04637',
        'priority': 5,
        'target_class': 'Transcription Factor',
        'pathway': 'Cellular Senescence',
        'description': 'p53 drives cellular senescence in skin cells. Persistent p53 activation depletes sebaceous gland progenitors (Blimp1+ cells) and impairs renewal.',
        'rationale': 'p53 is a master regulator of senescence. Modulating p53 activity (not complete inhibition) could reduce senescence while preserving tumor suppression.',
        'genetic_evidence': 'Persistent p53 activation depletes sebaceous gland progenitors',
        'drug_modality': ['p53 modulators', 'Senostatics'],
        'development_stage': 'Research',
        'novelty_score': 7.0,
        'druggability_score': 6.5,
        'safety_score': 5.5,
        'priority_score': 6.5,
        'known_inhibitors': [
            {'name': 'p53 activators (nutlin)', 'type': 'Small molecule', 'status': 'Research'},
        ],
        'screening_assay': 'Senescence-associated β-galactosidase, p21 expression',
        'validation_model': 'Aged mouse skin, senescent cell models'
    },
    'WNT5A': {
        'gene_name': 'Wingless-type 5A',
        'uniprot_id': 'P41221',
        'priority': 6,
        'target_class': 'Signaling Protein',
        'pathway': 'Wnt/β-catenin',
        'description': 'Wnt/β-catenin signaling regulates HFSC activation and epidermal regeneration. Androgen receptor activation antagonizes Wnt/β-catenin, delaying wound healing.',
        'rationale': 'Activating Wnt/β-catenin could overcome androgen-mediated inhibition and promote regeneration. Wnt agonists are in development for other indications.',
        'genetic_evidence': 'Wnt activation promotes HFSC activation and hair regeneration',
        'drug_modality': ['Wnt agonist', 'Porcupine inhibitor (for canonical Wnt)'],
        'development_stage': 'Research',
        'novelty_score': 8.0,
        'druggability_score': 7.0,
        'safety_score': 7.5,
        'priority_score': 7.5,
        'known_inhibitors': [
            {'name': 'Wnt agonists (Wnt3a, SKL)', 'type': 'Protein/small molecule', 'status': 'Research'},
            {'name': 'Porcupine inhibitors', 'type': 'Wnt inhibitor', 'status': 'Clinical (cancer)'},
        ],
        'screening_assay': 'β-catenin reporter assay, HFSC activation markers',
        'validation_model': 'Aged mouse skin, HFSC culture'
    },
    'SETDB1': {
        'gene_name': 'SET Domain Bifurcated 1 (Histone Methyltransferase)',
        'uniprot_id': 'Q15047',
        'priority': 7,
        'target_class': 'Epigenetic Regulator',
        'pathway': 'ERV Silencing/Transposable Elements',
        'description': 'Setdb1 maintains silencing of endogenous retroviruses (ERVs). Loss of Setdb1 in adult skin activates TEs, triggering antiviral immune responses and HFSC exhaustion.',
        'rationale': 'Setdb1 loss causes regenerative failure via ERV activation. Restoring Setdb1 or blocking downstream interferon signaling could reverse this phenotype.',
        'genetic_evidence': 'Setdb1 knockout in adult skin causes TE activation and hair loss (reversible with antiviral treatment)',
        'drug_modality': ['Epigenetic modulator', 'Antiviral agents'],
        'development_stage': 'Research',
        'novelty_score': 9.5,
        'druggability_score': 5.5,
        'safety_score': 7.0,
        'priority_score': 7.5,
        'known_inhibitors': [
            {'name': 'Setdb1 activators', 'type': 'Epigenetic', 'status': 'Research'},
        ],
        'screening_assay': 'ERV expression (LINE-1, MuLV), interferon response genes',
        'validation_model': 'Setdb1 conditional KO mice'
    },
    'TLR4': {
        'gene_name': 'Toll-like Receptor 4',
        'uniprot_id': 'O00206',
        'priority': 8,
        'target_class': 'Pattern Recognition Receptor',
        'pathway': 'Gut-Skin Axis/Innate Immunity',
        'description': 'TLR4 on keratinocytes/fibroblasts responds to gut-derived LPS and bacterial products, activating NF-κB and MMP production. Gut dysbiosis with aging increases systemic LPS.',
        'rationale': 'TLR4 inhibition could block gut-derived pro-aging signals. Topical TLR4 antagonists might avoid systemic immunosuppression.',
        'genetic_evidence': 'TLR4 activation by LPS promotes skin inflammation and MMP expression',
        'drug_modality': ['TLR4 antagonist', 'Gut microbiome modulation'],
        'development_stage': 'Research',
        'novelty_score': 8.0,
        'druggability_score': 7.5,
        'safety_score': 8.0,
        'priority_score': 7.8,
        'known_inhibitors': [
            {'name': 'TLR4 antagonists (eritoran)', 'type': 'Small molecule', 'status': 'Research (sepsis)'},
        ],
        'screening_assay': 'NF-κB reporter assay, IL-6 secretion',
        'validation_model': 'Germ-free vs colonized mice, aged skin models'
    }
}


# Priority targets for quick screening
SKIN_AGING_PRIORITY_TARGETS = [
    'COL17A1',  # Top priority - root cause of HFSC exhaustion
    'IL6',      # SASP key mediator, approved biologics exist
    'MMP1',     # Direct ECM degradation, druggable
    'WNT5A',    # Regeneration pathway
    'TERT',     # Telomere, high risk/reward
    'SETDB1',   # Novel epigenetic target
]


# Related MERFISH findings from skin atlas
SKIN_AGING_MERFISH_CORRELATES = {
    'TGFB2': -13.8,  # Downregulated in aged skin
    'PDGFA': -14.3,  # Downregulated  
    'TGFB1': -11.8,  # Downregulated
    'FGF7': -12.6,   # Downregulated
}
