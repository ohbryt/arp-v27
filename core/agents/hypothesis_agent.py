"""
ARP v25 - Hypothesis Agent
Auto hypothesis generation from literature and data

NEW in v25: Autonomous hypothesis generation based on targets and diseases
Based on Nature Medicine 2026 "Agentic framework for autonomous scientific discovery"
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json

@dataclass
class Hypothesis:
    """A generated research hypothesis"""
    id: str
    target: str
    disease: str
    description: str
    mechanism: str
    predicted_outcome: str
    supporting_evidence: List[str]
    testable_predictions: List[str]
    confidence: float  # 0-1
    priority: str  # high, medium, low
    created: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def __post_init__(self):
        if isinstance(self.created, str) and self.created == "auto":
            self.created = datetime.now().isoformat()

from dataclasses import dataclass, field, field

class HypothesisAgent:
    """
    Agent that generates research hypotheses.
    Analyzes targets, diseases, and literature to produce testable hypotheses.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.llm_provider = self.config.get("llm_provider", "groq")
        self.model = self.config.get("model", "llama-3.3-70b")
        self.hypotheses: List[Hypothesis] = []
        self.history: List[Dict] = []
    
    async def generate(
        self,
        target: str,
        disease: str,
        context: Optional[Dict] = None,
        num_hypotheses: int = 3
    ) -> List[Hypothesis]:
        """
        Generate hypotheses for a target-disease pair.
        
        Args:
            target: Target gene/protein
            disease: Disease area
            context: Additional context (literature, data, etc.)
            num_hypotheses: Number of hypotheses to generate
        
        Returns:
            List of generated hypotheses
        """
        context = context or {}
        
        # Build prompt for hypothesis generation
        prompt = self._build_prompt(target, disease, context)
        
        # Call LLM (simplified - would integrate with actual LLM)
        result = await self._call_llm(prompt)
        
        # Parse hypotheses from result
        hypotheses = self._parse_hypotheses(result, target, disease)
        
        # Limit to requested number
        hypotheses = hypotheses[:num_hypotheses]
        
        # Store and return
        self.hypotheses.extend(hypotheses)
        self.history.append({
            "target": target,
            "disease": disease,
            "num_generated": len(hypotheses),
            "timestamp": datetime.now().isoformat()
        })
        
        return hypotheses
    
    def _build_prompt(self, target: str, disease: str, context: Dict) -> str:
        """Build prompt for hypothesis generation"""
        context_str = ""
        if context.get("literature"):
            context_str += f"\nLiterature: {context['literature']}"
        if context.get("expression_data"):
            context_str += f"\nExpression: {context['expression_data']}"
        if context.get("previous_hypotheses"):
            context_str += f"\nPrevious: {context['previous_hypotheses']}"
        
        return f"""
You are a biomedical research hypothesis generator.

Generate testable hypotheses for targeting {target} in {disease}.

Consider:
1. Mechanism of action
2. Potential off-target effects
3. Biomarkers for patient selection
4. Combination therapy potential
5. Resistance mechanisms{context_str}

Generate exactly 3 hypotheses in JSON format:
[
  {{
    "description": "Clear hypothesis statement",
    "mechanism": "Molecular mechanism",
    "predicted_outcome": "Expected result",
    "supporting_evidence": ["evidence1", "evidence2"],
    "testable_predictions": ["prediction1", "prediction2"],
    "confidence": 0.8,
    "priority": "high"
  }}
]
"""
    
    async def _call_llm(self, prompt: str) -> str:
        """Call LLM for hypothesis generation using Groq"""
        try:
            from integration.groq_client import client
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM call failed: {e}")
            return "[]"
    
    def _parse_hypotheses(
        self,
        llm_response: str,
        target: str,
        disease: str
    ) -> List[Hypothesis]:
        """Parse LLM response into Hypothesis objects"""
        import uuid
        
        hypotheses = []
        try:
            # Try to parse as JSON
            if "[" in llm_response and "]" in llm_response:
                json_str = llm_response[llm_response.index("["):llm_response.rindex("]")+1]
                data = json.loads(json_str)
                
                for item in data:
                    h = Hypothesis(
                        id=f"hyp_{uuid.uuid4().hex[:8]}",
                        target=target,
                        disease=disease,
                        description=item.get("description", ""),
                        mechanism=item.get("mechanism", ""),
                        predicted_outcome=item.get("predicted_outcome", ""),
                        supporting_evidence=item.get("supporting_evidence", []),
                        testable_predictions=item.get("testable_predictions", []),
                        confidence=item.get("confidence", 0.5),
                        priority=item.get("priority", "medium")
                    )
                    hypotheses.append(h)
        except (json.JSONDecodeError, ValueError):
            pass
        
        return hypotheses
    
    def get_hypotheses(
        self,
        target: Optional[str] = None,
        disease: Optional[str] = None,
        min_confidence: float = 0.0
    ) -> List[Hypothesis]:
        """Get stored hypotheses with optional filtering"""
        results = self.hypotheses
        
        if target:
            results = [h for h in results if target.lower() in h.target.lower()]
        if disease:
            results = [h for h in results if disease.lower() in h.disease.lower()]
        if min_confidence > 0:
            results = [h for h in results if h.confidence >= min_confidence]
        
        return results
    
    def rank_hypotheses(
        self,
        hypotheses: List[Hypothesis] = None
    ) -> List[Hypothesis]:
        """Rank hypotheses by confidence and priority"""
        if hypotheses is None:
            hypotheses = self.hypotheses
        
        priority_weights = {"high": 3, "medium": 2, "low": 1}
        
        return sorted(
            hypotheses,
            key=lambda h: (h.confidence, priority_weights.get(h.priority, 0)),
            reverse=True
        )
    
    def export_hypotheses(self, format: str = "json") -> str:
        """Export hypotheses in specified format"""
        data = [
            {
                "id": h.id,
                "target": h.target,
                "disease": h.disease,
                "description": h.description,
                "mechanism": h.mechanism,
                "predicted_outcome": h.predicted_outcome,
                "supporting_evidence": h.supporting_evidence,
                "testable_predictions": h.testable_predictions,
                "confidence": h.confidence,
                "priority": h.priority,
                "created": h.created,
            }
            for h in self.hypotheses
        ]
        
        if format == "json":
            return json.dumps(data, indent=2)
        elif format == "csv":
            # Simple CSV export
            lines = ["id,target,disease,description,confidence,priority"]
            for h in data:
                lines.append(f'{h["id"]},{h["target"]},{h["disease"]},{h["description"]},{h["confidence"]},{h["priority"]}')
            return "\n".join(lines)
        
        return str(data)
