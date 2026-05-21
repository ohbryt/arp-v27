"""
ARP v25 - Router Module
Task routing based on target/disease matching
"""

from typing import Dict, List, Optional, Set
import re

class Router:
    """
    Routes tasks to appropriate agents based on target/disease.
    Maintains routing rules and patterns.
    """
    
    # Routing rules: pattern -> agent/task type
    DEFAULT_ROUTES = {
        "lung_cancer": "cancer_researcher",
        "nsclc": "cancer_researcher",
        "fibrosis": "fibrosis_researcher",
        "lung_fibrosis": "fibrosis_researcher",
        "cardiac_fibrosis": "fibrosis_researcher",
        "aging": "aging_researcher",
        "gut_aging": "aging_researcher",
        "sarcopenia": "sarcopenia_researcher",
    }
    
    TARGET_ROUTES = {
        "KDM4A": "epigenetic_researcher",
        "SLC7A11": "ferroptosis_researcher",
        "DGAT1": "lipid_researcher",
        "YARS2": "mitochondrial_researcher",
        "GLYXALASE_I": "aging_researcher",
        "BCAT2": "metabolism_researcher",
        "SLC7A5": "metabolism_researcher",
        "MTOR": "aging_researcher",
        "PF14": "delivery_researcher",
    }
    
    def __init__(self, custom_routes: Optional[Dict] = None):
        self.custom_routes = custom_routes or {}
        self.route_cache: Dict[str, str] = {}
    
    def route(self, target: str, disease: str) -> str:
        """Route a target/disease pair to appropriate agent"""
        cache_key = f"{target}:{disease}"
        if cache_key in self.route_cache:
            return self.route_cache[cache_key]
        
        # First try target-based routing
        for target_pattern, agent in self.TARGET_ROUTES.items():
            if self._match(target, target_pattern):
                self.route_cache[cache_key] = agent
                return agent
        
        # Then try disease-based routing
        for disease_pattern, agent in self.DEFAULT_ROUTES.items():
            if self._match(disease, disease_pattern):
                self.route_cache[cache_key] = agent
                return agent
        
        # Default fallback
        self.route_cache[cache_key] = "general_researcher"
        return "general_researcher"
    
    def _match(self, text: str, pattern: str) -> bool:
        """Check if text matches pattern (case insensitive)"""
        text_lower = text.lower().replace("_", " ").replace("-", " ")
        pattern_lower = pattern.lower().replace("_", " ").replace("-", " ")
        return pattern_lower in text_lower or text_lower in pattern_lower
    
    def get_available_routes(self) -> Dict[str, List[str]]:
        """Get all available routes"""
        return {
            "by_target": list(self.TARGET_ROUTES.keys()),
            "by_disease": list(self.DEFAULT_ROUTES.keys()),
        }
    
    def add_route(self, pattern: str, agent: str):
        """Add a custom route"""
        if pattern in self.TARGET_ROUTES:
            self.TARGET_ROUTES[pattern] = agent
        else:
            self.DEFAULT_ROUTES[pattern] = agent
