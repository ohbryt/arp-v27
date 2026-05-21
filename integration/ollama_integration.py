"""
Ollama Integration for ARP v24
=================================
Local LLM inference for biomedical research

Available models:
- gemma3:4b (3.3 GB) - General biomed
- clinic-copilot (9.0 GB) - Medical literature
- qwen3:14b (9.3 GB) - General reasoning
- deepseek-v3.1:671b - Cloud (671B params)

Usage:
    from integration.ollama_integration import OllamaBiomedLLM
    
    llm = OllamaBiomedLLM()
    
    # Medical literature analysis
    result = llm.analyze_literature("DGAT1 siRNA lung cancer delivery")
    
    # Target validation
    result = llm.validate_target("CD36", context="cancer metabolism")
    
    # Drug mechanism explanation
    result = llm.explain_mechanism("How does DGAT1 inhibition work in cancer?")
"""

import os
import json
import subprocess
from typing import Dict, List, Any, Optional, Union
from pathlib import Path


class OllamaBiomedLLM:
    """
    Ollama-powered LLM for biomedical research
    
    Features:
    - Local inference (privacy-preserving)
    - Medical literature analysis
    - Target validation
    - Drug mechanism explanation
    - Multi-model support
    """
    
    def __init__(
        self,
        default_model: str = "clinic-copilot",
        fallback_model: str = "gemma3:4b"
    ):
        self.default_model = default_model
        self.fallback_model = fallback_model
        self._available_models = None
        self._check_models()
    
    def _check_models(self) -> List[str]:
        """Check which Ollama models are available"""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                models = []
                for line in lines[1:]:  # Skip header
                    if line.strip():
                        parts = line.split()
                        if parts:
                            models.append(parts[0])
                self._available_models = models
            else:
                self._available_models = []
                
        except Exception as e:
            print(f"⚠️ Ollama not available: {e}")
            self._available_models = []
        
        return self._available_models or []
    
    def _run_model(
        self,
        model: str,
        prompt: str,
        system: str = None,
        timeout: int = 120
    ) -> Dict[str, Any]:
        """
        Run Ollama model and return response
        
        Args:
            model: Model name (e.g., "clinic-copilot", "gemma3:4b")
            prompt: User prompt
            system: Optional system prompt
            timeout: Timeout in seconds
        
        Returns:
            Response dictionary with text and metadata
        """
        import ollama
        
        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            
            response = ollama.chat(
                model=model,
                messages=messages,
                options={
                    "temperature": 0.3,  # Lower temp for factual tasks
                    "num_predict": 512  # Limit output length
                }
            )
            
            return {
                "status": "success",
                "model": model,
                "response": response["message"]["content"],
                "done": True
            }
            
        except Exception as e:
            return {
                "status": "error",
                "model": model,
                "error": str(e)
            }
    
    def analyze_literature(
        self,
        topic: str,
        model: str = None
    ) -> Dict[str, Any]:
        """
        Analyze medical/scientific literature on a topic
        
        Args:
            topic: Research topic (e.g., "DGAT1 siRNA delivery")
            model: Optional model override
        
        Returns:
            Literature analysis
        """
        model = model or self.default_model
        
        system = """You are a biomedical research assistant. Analyze scientific literature 
and provide accurate, evidence-based summaries. Focus on:
- Key findings and mechanisms
- Clinical relevance
- Gaps and future directions
Format your response clearly with bullet points."""
        
        prompt = f"""Analyze the current state of research on: {topic}

Provide:
1. Key mechanisms
2. Current evidence
3. Clinical applications
4. Research gaps
5. Future directions

Keep it concise (3-5 bullet points per section)."""
        
        result = self._run_model(model, prompt, system)
        result["topic"] = topic
        return result
    
    def validate_target(
        self,
        target: str,
        context: str = "cancer",
        model: str = None
    ) -> Dict[str, Any]:
        """
        Validate a drug target for a specific disease context
        
        Args:
            target: Target name (e.g., "DGAT1", "CD36")
            context: Disease context (e.g., "cancer", "metabolic disease")
            model: Optional model override
        
        Returns:
            Target validation analysis
        """
        model = model or self.default_model
        
        system = """You are a drug discovery expert. Evaluate target appropriateness 
for disease treatment. Consider:
- Scientific rationale
- Clinical evidence
- Technical feasibility
- Competition"""
        
        prompt = f"""Evaluate {target} as a drug target for {context}.

Provide:
1. Scientific rationale (why this target matters)
2. Supporting evidence level (strong/moderate/weak)
3. Key challenges
4. Development recommendations

Be critical and concise."""
        
        result = self._run_model(model, prompt, system)
        result["target"] = target
        result["context"] = context
        return result
    
    def explain_mechanism(
        self,
        question: str,
        model: str = None
    ) -> Dict[str, Any]:
        """
        Explain a biological/drug mechanism
        
        Args:
            question: Mechanism question (e.g., "How does DGAT1 inhibition work?")
            model: Optional model override
        
        Returns:
            Mechanism explanation
        """
        model = model or self.default_model
        
        system = """You are a molecular biology expert. Explain mechanisms clearly 
and accurately. Use appropriate technical terms but keep it understandable."""
        
        prompt = f"""{question}

Provide a clear, concise explanation:
- Key molecular players
- Mechanism steps
- Expected outcomes
- Potential side effects"""
        
        result = self._run_model(model, prompt, system)
        result["question"] = question
        return result
    
    def summarize_paper(
        self,
        title: str,
        abstract: str = None,
        model: str = None
    ) -> Dict[str, Any]:
        """
        Summarize a scientific paper
        
        Args:
            title: Paper title
            abstract: Paper abstract (optional)
            model: Optional model override
        
        Returns:
            Paper summary
        """
        model = model or self.default_model
        
        system = """You are a scientific reviewer. Summarize papers accurately, 
identifying key contributions and limitations."""
        
        if abstract:
            prompt = f"""Title: {title}

Abstract: {abstract}

Summarize:
1. Main findings (1-2 sentences)
2. Key methods used
3. Major conclusions
4. Significance for the field"""
        else:
            prompt = f"""Summarize the key aspects of this paper: {title}

Provide:
1. Likely research focus
2. Expected key findings
3. Potential impact"""
        
        result = self._run_model(model, prompt, system)
        result["title"] = title
        return result
    
    def generate_research_ideas(
        self,
        target: str,
        disease: str,
        model: str = None
    ) -> Dict[str, Any]:
        """
        Generate research hypotheses for a target-disease pair
        
        Args:
            target: Drug target
            disease: Disease context
            model: Optional model override
        
        Returns:
            Research hypotheses
        """
        model = model or self.fallback_model  # Use larger model for creative tasks
        
        system = """You are a creative researcher. Generate innovative but feasible 
research ideas. Consider:
- Novel mechanisms
- Combination approaches
- Translation potential"""
        
        prompt = f"""Generate 5 research hypotheses for targeting {target} in {disease}.

For each hypothesis provide:
1. Brief description
2. Scientific rationale
3. Potential approach
4. Expected challenge

Be specific and innovative."""
        
        result = self._run_model(model, prompt, system)
        result["target"] = target
        result["disease"] = disease
        return result
    
    def list_available_models(self) -> List[str]:
        """List available Ollama models"""
        if self._available_models is None:
            self._check_models()
        return self._available_models or []
    
    def quick_query(
        self,
        question: str,
        model: str = None
    ) -> str:
        """
        Quick query to any available model
        
        Args:
            question: Question to ask
            model: Model to use (default: first available)
        
        Returns:
            Response text
        """
        models = self.list_available_models()
        if not models:
            return "No Ollama models available"
        
        model = model or models[0]
        result = self._run_model(model, question)
        
        if result["status"] == "success":
            return result["response"]
        else:
            return f"Error: {result.get('error', 'Unknown')}"


def quick_analyze(topic: str, model: str = "clinic-copilot") -> str:
    """
    Quick literature analysis helper
    
    Usage:
        result = quick_analyze("DGAT1 siRNA lung cancer delivery")
    """
    llm = OllamaBiomedLLM(default_model=model)
    result = llm.analyze_literature(topic)
    return result.get("response", result.get("error", "Failed"))


def quick_target_validate(target: str, disease: str = "cancer") -> str:
    """
    Quick target validation helper
    
    Usage:
        result = quick_target_validate("CD36", "lung cancer")
    """
    llm = OllamaBiomedLLM()
    result = llm.validate_target(target, disease)
    return result.get("response", result.get("error", "Failed"))


# Demo function
def demo():
    """Demo Ollama integration"""
    print("=" * 70)
    print("Ollama Biomedical LLM Integration Demo")
    print("=" * 70)
    
    llm = OllamaBiomedLLM()
    
    # Check available models
    models = llm.list_available_models()
    print(f"\nAvailable models: {len(models)}")
    for m in models:
        print(f"  - {m}")
    
    if not models:
        print("\n⚠️ No Ollama models found")
        print("Install models with: ollama pull <model>")
        return
    
    print("\n" + "-" * 50)
    print("Testing: Target validation (CD36 in cancer)")
    print("-" * 50)
    
    result = llm.validate_target("CD36", "cancer")
    print(f"\nModel: {result.get('model')}")
    print(f"Status: {result.get('status')}")
    print(f"\nResponse:\n{result.get('response', 'N/A')}")
    
    print("\n" + "-" * 50)
    print("Testing: Mechanism explanation")
    print("-" * 50)
    
    result = llm.explain_mechanism("How does DGAT1 inhibition suppress tumor growth?")
    print(f"\nResponse:\n{result.get('response', 'N/A')}")


if __name__ == "__main__":
    demo()