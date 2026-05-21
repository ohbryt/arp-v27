"""
ARP v25 - Target Registry Module
Central registry of all validated research targets
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json

@dataclass
class Target:
    """A research target entry"""
    id: str
    name: str
    gene_id: str
    target_type: str  # enzyme, transporter, receptor, etc.
    pathway: str
    disease_associations: List[str]
    priority: int  # 1-5, 1 is highest
    inhibitors: List[Dict[str, Any]] = field(default_factory=list)
    biomarkers: List[str] = field(default_factory=list)
    status: str = "active"  # active, paused, validated, abandoned
    notes: str = ""
    created: str = field(default_factory=lambda: datetime.now().isoformat())
    updated: str = field(default_factory=lambda: datetime.now().isoformat())

class TargetRegistry:
    """
    Central registry for all research targets.
    Provides lookup, filtering, and management.
    """
    
    def __init__(self):
        self.targets: Dict[str, Target] = {}
        self._init_default_targets()
    
    def _init_default_targets(self):
        """Initialize with default targets from v25"""
        default_targets = [
            Target(
                id="KDM4A_SLC7A11",
                name="KDM4A-SLC7A11 Axis",
                gene_id="COMBO",
                target_type="epigenetic-ferroptosis",
                pathway="H3K9me3 demethylation → SLC7A11 transcription",
                disease_associations=["NSCLC", "lung cancer", "osteosarcoma"],
                priority=1,
                inhibitors=[
                    {"name": "JIB-04", "target": "KDM4A/B/C/D", "ic50": "~200nM"},
                    {"name": "KDM4-IN-4", "target": "KDM4A", "ic50": "~1μM"},
                    {"name": "NCDM-32B", "target": "KDM4A/B/C", "ic50": "3.0μM"},
                ],
                biomarkers=["KDM4A expression", "SLC7A11 expression", "H3K9me3"],
                notes="Triple combo with DGAT1 + SLC7A11 inhibitors"
            ),
            Target(
                id="DGAT1",
                name="Diacylglycerol O-Acyltransferase 1",
                gene_id="DGAT1",
                target_type="enzyme",
                pathway="Triglyceride synthesis",
                disease_associations=["NSCLC", "cancer", "metabolic disease"],
                priority=1,
                inhibitors=[
                    {"name": "PF-06450309", "target": "DGAT1", "ic50": "8nM"},
                    {"name": "A922500", "target": "DGAT1", "ic50": "13nM"},
                ],
                biomarkers=["Lipid droplets", "TG levels", "ROS"],
                notes="PF14-siDGAT1 delivery system"
            ),
            Target(
                id="SLC7A11",
                name="Solute Carrier 7A11",
                gene_id="SLC7A11",
                target_type="transporter",
                pathway="Cystine/glutamate antiporter",
                disease_associations=["NSCLC", "ferroptosis-resistant cancers"],
                priority=1,
                inhibitors=[
                    {"name": "Erastin", "target": "SLC7A11", "ic50": "~100nM"},
                    {"name": "Sulfasalazine", "target": "SLC7A11", "ic50": "~50μM"},
                ],
                biomarkers=["SLC7A11 expression", "GSH levels", "Lipid ROS"],
                notes="Ferroptosis target"
            ),
            Target(
                id="GLYXALASE_I",
                name="Glyoxalase I",
                gene_id="GLOD1",
                target_type="enzyme",
                pathway="Methylglyoxal detoxification",
                disease_associations=["Aging", "Diabetes", "Neurodegeneration"],
                priority=2,
                inhibitors=[
                    {"name": "S-allyl cysteine", "target": "Glo-I", "source": "garlic"},
                    {"name": "Flavonoids", "target": "Glo-I", "source": "natural"},
                ],
                biomarkers=["Glo-I activity", "Methylglyoxal levels"],
                notes="NEW: Anti-aging target (May 2026)"
            ),
            Target(
                id="BCAT2",
                name="Branched-Chain Amino Acid Transaminase 2",
                gene_id="BCAT2",
                target_type="enzyme",
                pathway="BCAA metabolism",
                disease_associations=["Lung fibrosis", "Cardiac fibrosis"],
                priority=2,
                biomarkers=["BCAT2 expression", "BCAA levels"],
                notes="NEW: BCAA-KDM4A-fibrosis connection (April 2026)"
            ),
            Target(
                id="SLC7A5",
                name="LAT1 (Large Neutral Amino Acid Transporter)",
                gene_id="SLC7A5",
                target_type="transporter",
                pathway="Large neutral amino acid uptake",
                disease_associations=["Cancer", "IPF", "Cardiac fibrosis"],
                priority=2,
                inhibitors=[
                    {"name": "JPH203/Nanvuranlat", "target": "SLC7A5", "stage": "Phase 1/2"},
                ],
                biomarkers=["SLC7A5 expression", "mTORC1 activity"],
                notes="Drug repositioning candidate"
            ),
            Target(
                id="MTOR",
                name="mTOR",
                gene_id="MTOR",
                target_type="kinase",
                pathway="Cell growth, autophagy",
                disease_associations=["Aging", "Cancer", "Fibrosis"],
                priority=2,
                inhibitors=[
                    {"name": "Rapamycin", "target": "mTORC1", "approved": True},
                    {"name": "Citrulline", "target": "mTOR", "natural": True},
                ],
                biomarkers=["p-S6K1", "mTOR activity", "Autophagy"],
                notes="Citrulline = endogenous mTOR inhibitor"
            ),
            Target(
                id="YARS2",
                name="Tyrosyl-tRNA Synthetase 2",
                gene_id="YARS2",
                target_type="enzyme",
                pathway="Mitochondrial protein synthesis",
                disease_associations=["Lung cancer", "Mitochondrial disorders"],
                priority=1,
                delivery=["PF14 peptide"],
                biomarkers=["YARS2 expression", "Mitochondrial function"],
                notes="PF14-siYARS2 delivery (N/P 1-4)"
            ),
            Target(
                id="PF14",
                name="PepFect 14",
                gene_id="N/A",
                target_type="delivery_peptide",
                pathway="siRNA delivery, endosomal escape",
                disease_associations=["Lung cancer (delivery)"],
                priority=1,
                specs={
                    "NP_ratio": "1-4 (CORRECTED from 5-10)",
                    "particle_size": "~119nm",
                    "lung_enrichment": "16-350x",
                    "cytotoxicity": "Low",
                },
                biomarkers=["Transfection efficiency", "Epithelial tropism"],
                notes="PF14-siDGAT1 protocol complete"
            ),
        ]
        
        for target in default_targets:
            self.targets[target.id] = target
    
    def get(self, target_id: str) -> Optional[Target]:
        """Get a target by ID"""
        return self.targets.get(target_id)
    
    def search(self, query: str) -> List[Target]:
        """Search targets by name, disease, or pathway"""
        query_lower = query.lower()
        results = []
        for target in self.targets.values():
            if (query_lower in target.name.lower() or
                query_lower in target.id.lower() or
                any(query_lower in d.lower() for d in target.disease_associations) or
                query_lower in target.pathway.lower()):
                results.append(target)
        return results
    
    def filter_by_priority(self, max_priority: int) -> List[Target]:
        """Filter targets by maximum priority"""
        return [t for t in self.targets.values() if t.priority <= max_priority]
    
    def filter_by_disease(self, disease: str) -> List[Target]:
        """Get targets associated with a disease"""
        disease_lower = disease.lower()
        return [
            t for t in self.targets.values()
            if any(disease_lower in d.lower() for d in t.disease_associations)
        ]
    
    def add_target(self, target: Target):
        """Add a new target"""
        self.targets[target.id] = target
    
    def list_all(self) -> List[Target]:
        """List all targets"""
        return list(self.targets.values())
    
    def to_dict(self) -> Dict:
        """Export registry as dict"""
        return {
            "targets": {
                k: {
                    "id": v.id,
                    "name": v.name,
                    "gene_id": v.gene_id,
                    "type": v.target_type,
                    "pathway": v.pathway,
                    "diseases": v.disease_associations,
                    "priority": v.priority,
                    "status": v.status,
                }
                for k, v in self.targets.items()
            }
        }
