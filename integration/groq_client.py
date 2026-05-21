"""
Groq API Integration for ARP v24
================================
Ultra-fast LLM inference for biomedical research

Key Features:
- 14,400 requests/day (free tier)
- Llama 3.3 70B: ~0.6s per summary (17x faster than Ollama Qwen 2.5 32B!)
- Biomedical literature summarization
- Real-time PubMed analysis
- Research report generation

API Key: Set via environment variable GROQ_API_KEY
"""

import os
from groq import Groq
from typing import Optional, List, Dict, Any

# Groq API Key - Set via environment variable GROQ_API_KEY
# Or use: export GROQ_API_KEY="your-key-here"
# DO NOT hardcode API keys in production!

client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))

if not os.environ.get("GROQ_API_KEY"):
    print("Warning: GROQ_API_KEY not set in environment")

# Available models on Groq (as of 2026)
GROQ_MODELS = {
    "llama-3.3-70b-versatile": {
        "name": "Llama 3.3 70B Versatile",
        "context": 131072,
        "speed": "fastest",
        "best_for": "Complex reasoning, long documents"
    },
    "llama-3.1-8b": {
        "name": "Llama 3.1 8B",
        "context": 128000,
        "speed": "fast",
        "best_for": "Quick summaries, simple tasks"
    },
    "mixtral-8x7b": {
        "name": "Mixtral 8x7B",
        "context": 32000,
        "speed": "very fast",
        "best_for": "Balanced performance"
    },
    "qwen-2.5-32b": {
        "name": "Qwen 2.5 32B",
        "context": 32000,
        "speed": "fast",
        "best_for": "Coding, reasoning"
    }
}

DEFAULT_MODEL = "llama-3.3-70b-versatile"


def summarize(text: str, model: str = DEFAULT_MODEL, max_length: int = 500) -> str:
    """
    Ultra-fast text summarization using Groq
    
    Args:
        text: Text to summarize
        model: Groq model to use
        max_length: Maximum summary length in words
    
    Returns:
        Summarized text
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": f"You are a biomedical research assistant. Summarize the following text concisely in {max_length} words or less. Focus on key findings, methods, and conclusions."
                },
                {
                    "role": "user",
                    "content": text[:15000]  # Truncate to avoid token limits
                }
            ],
            temperature=0.3,
            max_tokens=max_length * 2
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"


def analyze_paper(abstract: str, model: str = DEFAULT_MODEL) -> Dict[str, Any]:
    """
    Analyze a scientific paper abstract
    
    Returns structured analysis with:
    - Key findings
    - Methods
    - Limitations
    - Clinical relevance
    - Novelty score
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": """You are a biomedical research analyst. Analyze the following scientific abstract and return a structured JSON with:
{
    "key_findings": "Main discoveries (2-3 sentences)",
    "methods": "Study design and methods used",
    "limitations": "Potential weaknesses or gaps",
    "clinical_relevance": "Impact on medical practice or drug discovery",
    "novelty_score": 1-10,
    "target_genes": ["list of genes/proteins mentioned"],
    "disease_area": "Primary disease context"
}
Return ONLY valid JSON, no additional text."""
                },
                {
                    "role": "user",
                    "content": abstract[:15000]
                }
            ],
            temperature=0.1,
            max_tokens=800
        )
        import json
        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        return {"error": str(e)}


def literature_review(topic: str, num_papers: int = 5, model: str = DEFAULT_MODEL) -> str:
    """
    Generate a literature review on a biomedical topic
    
    Args:
        topic: Research topic or question
        num_papers: Number of key papers to reference
        model: Groq model to use
    
    Returns:
        Formatted literature review
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": f"""You are a biomedical research scientist. Write a comprehensive literature review on the topic below. 

Structure your response as:
1. Background/Introduction
2. Key Mechanisms/Pathways
3. Current Therapeutic Approaches
4. Emerging Targets
5. Future Directions
6. References (cite key papers with PMID if known)

Focus on: {topic}
"""
                },
                {
                    "role": "user",
                    "content": topic
                }
            ],
            temperature=0.4,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"


def generate_hypothesis(target: str, disease: str, model: str = DEFAULT_MODEL) -> str:
    """
    Generate a testable scientific hypothesis
    
    Args:
        target: Gene/protein target
        disease: Disease of interest
        model: Groq model
    
    Returns:
        Hypothesis with mechanism and predictions
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": """You are a biomedical research scientist. Generate a testable scientific hypothesis following this format:

**Hypothesis**: [Clear, testable statement]

**Mechanism**: [Proposed biological mechanism]

**Predictions**:
1. [Specific, falsifiable prediction 1]
2. [Specific, falsifiable prediction 2]
3. [Specific, falsifiable prediction 3]

**Experimental Approach**: [How you would test this]

**Potential Impact**: [Significance to the field]

Use current knowledge about the target and disease. Be specific about molecular mechanisms."""
                },
                {
                    "role": "user",
                    "content": f"Target: {target}\nDisease: {disease}"
                }
            ],
            temperature=0.5,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"


def classify_compound(compound_info: str, model: str = DEFAULT_MODEL) -> Dict[str, Any]:
    """
    Classify a compound for drug discovery potential
    
    Args:
        compound_info: Name, structure, or description of compound
        model: Groq model
    
    Returns:
        Classification with drug-likeness, targets, indications
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": """You are a medicinal chemist. Analyze this compound and return JSON:

{
    "compound_name": "Name if known",
    "drug_class": "Classification (e.g., small molecule, peptide, natural product)",
    "mechanism": "Known or proposed mechanism of action",
    "therapeutic_indications": ["list of potential uses"],
    "druggability_score": 1-10,
    "admet_concerns": ["potential ADMET issues"],
    "structural_highlights": "Key structural features for activity",
    "similar_drugs": ["reference drugs with similar mechanisms"]
}

Return ONLY valid JSON."""
                },
                {
                    "role": "user",
                    "content": compound_info
                }
            ],
            temperature=0.2,
            max_tokens=600
        )
        import json
        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        return {"error": str(e)}


def batch_summarize(texts: List[str], model: str = DEFAULT_MODEL) -> List[str]:
    """
    Batch summarize multiple texts
    
    Args:
        texts: List of texts to summarize
        model: Groq model
    
    Returns:
        List of summaries
    """
    results = []
    for text in texts:
        summary = summarize(text, model)
        results.append(summary)
    return results


def stream_chat(message: str, system_prompt: str = None, model: str = DEFAULT_MODEL):
    """
    Stream chat completion for real-time interaction
    
    Args:
        message: User message
        system_prompt: Optional system prompt
        model: Groq model
    
    Yields:
        Chunks of the response
    """
    if system_prompt is None:
        system_prompt = "You are a helpful biomedical research assistant."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message}
    ]

    try:
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            temperature=0.5
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        yield f"Error: {str(e)}"


def get_usage() -> Dict[str, Any]:
    """
    Get current API usage (approximation based on rate limits)
    
    Returns:
        Usage information
    """
    return {
        "daily_limit": 14400,
        "model": DEFAULT_MODEL,
        "available_models": list(GROQ_MODELS.keys()),
        "status": "active" if GROQ_API_KEY else "not_configured"
    }


if __name__ == "__main__":
    # Test the Groq integration
    print("🚀 Groq API for ARP v24")
    print("=" * 50)
    print(f"Status: {get_usage()['status']}")
    print(f"Default Model: {GROQ_MODELS[DEFAULT_MODEL]['name']}")
    print(f"Context Window: {GROQ_MODELS[DEFAULT_MODEL]['context']:,} tokens")
    print()
    
    # Example: Summarize a paper abstract
    test_abstract = """
    Background: Metabolic dysfunction-associated steatotic liver disease (MASLD) 
    affects approximately 25% of the global population. Farnesoid X receptor (FXR) 
    agonists have shown promise in treating MASLD/MASH. 
    
    Methods: We conducted a phase 3 randomized controlled trial of obeticholic acid 
    (INT-747) in 931 patients with MASH and stage 2-3 fibrosis. Primary endpoint was 
    fibrosis improvement by >=1 stage without worsening of MASH.
    
    Results: At 18 months, 22.4% of patients receiving obeticholic acid 25mg achieved 
    the primary endpoint versus 9.6% in placebo (P<0.001). The most common adverse 
    event was pruritus (28% vs 7% placebo).
    
    Conclusion: Obeticholic acid significantly improves fibrosis in patients with MASH.
    """
    
    print("📄 Testing Paper Analysis:")
    print("-" * 50)
    analysis = analyze_paper(test_abstract)
    for key, value in analysis.items():
        print(f"{key}: {value}")
