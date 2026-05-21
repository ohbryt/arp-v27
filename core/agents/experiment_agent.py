"""
ARP v25 - Experiment Design Agent
Auto experimental protocol generation

NEW in v25: Autonomous experiment design based on hypotheses
Part of the agentic framework for scientific discovery
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json

@dataclass
class ExperimentProtocol:
    """A designed experimental protocol"""
    id: str
    hypothesis_id: str
    title: str
    objective: str
    method: str
    readouts: List[str]
    controls: List[str]
    sample_size: int
    duration_days: int
    resources: List[str]
    steps: List[Dict[str, str]]
    expected_results: str
    statistical_analysis: str
    created: str = field(default_factory=lambda: datetime.now().isoformat())

class ExperimentAgent:
    """
    Agent that designs experimental protocols from hypotheses.
    Takes a hypothesis and generates a complete experimental plan.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.llm_provider = self.config.get("llm_provider", "groq")
        self.model = self.config.get("model", "llama-3.3-70b")
        self.protocols: List[ExperimentProtocol] = []
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, Any]:
        """Load experiment templates for common assays"""
        return {
            "in_vitro": {
                "cell_viability": {
                    "method": "CCK-8 assay",
                    "readouts": ["Cell viability %", "IC50"],
                    "duration_days": 4,
                    "steps": [
                        {"step": 1, "action": "Seed cells in 96-well plate", "time": "Day 0"},
                        {"step": 2, "action": "Treat with compound at varying concentrations", "time": "Day 1"},
                        {"step": 3, "action": "Add CCK-8 reagent", "time": "Day 3 or 4"},
                        {"step": 4, "action": "Measure absorbance at 450nm", "time": "Day 3 or 4"},
                    ]
                },
                "qpcr": {
                    "method": "Quantitative PCR",
                    "readouts": ["mRNA expression", "ΔΔCt"],
                    "duration_days": 3,
                    "steps": [
                        {"step": 1, "action": "Treat cells with compound", "time": "Day 0"},
                        {"step": 2, "action": "Extract RNA", "time": "Day 2"},
                        {"step": 3, "action": "cDNA synthesis", "time": "Day 2"},
                        {"step": 4, "action": "qPCR amplification", "time": "Day 3"},
                    ]
                },
                "western_blot": {
                    "method": "Western Blot",
                    "readouts": ["Protein expression", "Band intensity"],
                    "duration_days": 4,
                    "steps": [
                        {"step": 1, "action": "Treat cells", "time": "Day 0"},
                        {"step": 2, "action": "Lyse cells, extract protein", "time": "Day 3"},
                        {"step": 3, "action": "Run SDS-PAGE", "time": "Day 3"},
                        {"step": 4, "action": "Transfer to membrane, antibody staining", "time": "Day 4"},
                    ]
                },
                "ferroptosis_assay": {
                    "method": "Ferroptosis detection",
                    "readouts": ["Lipid ROS", "GSH levels", "GPX4 activity"],
                    "duration_days": 4,
                    "steps": [
                        {"step": 1, "action": "Treat cells with compound ± erastin", "time": "Day 0"},
                        {"step": 2, "action": "Stain with C11-BODIPY for lipid ROS", "time": "Day 2"},
                        {"step": 3, "action": "Measure with flow cytometry", "time": "Day 2"},
                        {"step": 4, "action": "GSSG/GSH ratio measurement", "time": "Day 3"},
                    ]
                },
            },
            "in_vivo": {
                "xenograft": {
                    "method": "Tumor xenograft model",
                    "readouts": ["Tumor volume", "Weight", "Survival"],
                    "duration_days": 30,
                    "steps": [
                        {"step": 1, "action": "Inject cancer cells in nude mice", "time": "Day 0"},
                        {"step": 2, "action": "Randomize and treat", "time": "Day 7"},
                        {"step": 3, "action": "Monitor tumor growth", "time": "Days 7-35"},
                        {"step": 4, "action": "Harvest tissues", "time": "Day 35"},
                    ]
                },
                "fibrosis_model": {
                    "method": "Bleomycin-induced fibrosis",
                    "readouts": ["Ashcroft score", "Hydroxyproline", "α-SMA"],
                    "duration_days": 21,
                    "steps": [
                        {"step": 1, "action": "Intratracheal bleomycin installation", "time": "Day 0"},
                        {"step": 2, "action": "Treat with compound", "time": "Day 1-21"},
                        {"step": 3, "action": "Harvest lungs", "time": "Day 21"},
                        {"step": 4, "action": "Histology and biochemistry", "time": "Day 21-24"},
                    ]
                },
            }
        }
    
    async def design(
        self,
        hypothesis,
        model: str = "in_vitro",
        assay_type: Optional[str] = None,
        resources: Optional[List[str]] = None
    ) -> ExperimentProtocol:
        """
        Design an experimental protocol from a hypothesis.
        
        Args:
            hypothesis: HypothesisAgent.Hypothesis object
            model: "in_vitro" or "in_vivo"
            assay_type: Specific assay type (auto-selected if None)
            resources: Available resources
        
        Returns:
            ExperimentProtocol
        """
        resources = resources or []
        
        # Auto-select assay type if not specified
        if assay_type is None:
            assay_type = self._select_assay(hypothesis, model)
        
        # Get template
        template = self.templates.get(model, {}).get(assay_type, {})
        
        # Generate protocol
        protocol = await self._generate_protocol(hypothesis, model, assay_type, template, resources)
        
        self.protocols.append(protocol)
        return protocol
    
    def _select_assay(self, hypothesis, model: str) -> str:
        """Select appropriate assay based on hypothesis"""
        target = hypothesis.target.lower()
        mechanism = hypothesis.mechanism.lower()
        
        if "ferroptosis" in mechanism or "s7c11" in target:
            return "ferroptosis_assay"
        elif "viability" in mechanism or "toxicity" in mechanism:
            return "cell_viability"
        elif "expression" in mechanism or "mrna" in mechanism:
            return "qpcr"
        elif "protein" in mechanism:
            return "western_blot"
        else:
            return "cell_viability"
    
    async def _generate_protocol(
        self,
        hypothesis,
        model: str,
        assay_type: str,
        template: Dict,
        resources: List[str]
    ) -> ExperimentProtocol:
        """Generate a complete protocol"""
        import uuid
        
        # Build protocol from template and hypothesis
        protocol = ExperimentProtocol(
            id=f"prot_{uuid.uuid4().hex[:8]}",
            hypothesis_id=hypothesis.id,
            title=f"{assay_type.replace('_', ' ').title()} for {hypothesis.target} in {hypothesis.disease}",
            objective=f"Test hypothesis: {hypothesis.description}",
            method=template.get("method", assay_type),
            readouts=template.get("readouts", []),
            controls=self._get_default_controls(model),
            sample_size=self._calculate_sample_size(model),
            duration_days=template.get("duration_days", 7),
            resources=resources or ["Cell culture", "Compound", "Standard reagents"],
            steps=template.get("steps", []),
            expected_results=hypothesis.predicted_outcome,
            statistical_analysis=self._get_statistical_method(model)
        )
        
        return protocol
    
    def _get_default_controls(self, model: str) -> List[str]:
        """Get default controls for model"""
        if model == "in_vitro":
            return ["Untreated control", "Vehicle control", "Positive control"]
        else:
            return ["Sham control", "Model control", "Positive control"]
    
    def _calculate_sample_size(self, model: str) -> int:
        """Calculate sample size"""
        if model == "in_vitro":
            return 3  # Biological replicates
        else:
            return 8  # Animals per group
    
    def _get_statistical_method(self, model: str) -> str:
        """Get appropriate statistical method"""
        if model == "in_vitro":
            return "Student's t-test (two-tailed), ANOVA for multiple comparisons"
        else:
            return "Mann-Whitney U test, Kaplan-Meier survival analysis"
    
    def get_protocols(
        self,
        hypothesis_id: Optional[str] = None
    ) -> List[ExperimentProtocol]:
        """Get stored protocols"""
        if hypothesis_id:
            return [p for p in self.protocols if p.hypothesis_id == hypothesis_id]
        return self.protocols
    
    def export_protocol(self, protocol_id: str, format: str = "markdown") -> str:
        """Export protocol in specified format"""
        protocol = next((p for p in self.protocols if p.id == protocol_id), None)
        if not protocol:
            return "Protocol not found"
        
        if format == "markdown":
            return self._to_markdown(protocol)
        elif format == "json":
            return json.dumps(protocol.__dict__, indent=2)
        
        return str(protocol)
    
    def _to_markdown(self, protocol: ExperimentProtocol) -> str:
        """Convert protocol to markdown format"""
        steps_md = "\n".join(
            f"{s['step']}. **{s['action']}** ({s['time']})"
            for s in protocol.steps
        )
        
        return f"""# {protocol.title}

## Objective
{protocol.objective}

## Method
{protocol.method}

## Readouts
{', '.join(protocol.readouts)}

## Controls
{', '.join(protocol.controls)}

## Sample Size
{protocol.sample_size}

## Duration
{protocol.duration_days} days

## Resources
{', '.join(protocol.resources)}

## Steps
{steps_md}

## Expected Results
{protocol.expected_results}

## Statistical Analysis
{protocol.statistical_analysis}
"""
