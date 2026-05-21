"""
AURORA Integration for ARP v24
================================
Multimodal omics integration for drug discovery

Based on: Chen, J., et al. (2026) Cell Metabolism
"A Generative AI Framework Unifies Human Multi-omics to Model Aging, Metabolic Health and Intervention Response"

Usage:
    from integration.aurora_integration import AuroraResearcher
    
    researcher = AuroraResearcher()
    
    # Configure multi-omics datasets
    researcher.configure_modality("transcriptome", adata, sample_id="sample", labels={"age": 65})
    researcher.configure_modality("proteome", adata2, sample_id="sample", labels={"age": 65})
    
    # Train model
    model = researcher.train_model(project_name="masld_study")
    
    # Get embeddings and reconstruct modalities
    embeddings = researcher.get_embeddings(modality="transcriptome")
    reconstructed = researcher.reconstruct_modality("proteome", embeddings)
"""

import os
import sys
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import json


class AuroraResearcher:
    """
    AURORA-powered researcher for multimodal omics integration
    
    Integrates with ARP v24 to:
    - Validate targets across multiple omics layers
    - Discover biomarkers from multi-omics data
    - Model biological age and intervention response
    - Reconstruct missing modalities
    """
    
    def __init__(self, model_dir: str = ".models/aurora/"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.aurora_model = None
        self.datasets = {}
        self._initialized = False
        self._aurora_available = None
    
    def _check_aurora(self) -> bool:
        """Check if AURORA is available"""
        if self._aurora_available is not None:
            return self._aurora_available
        
        try:
            sys.path.insert(0, 'AURORA')
            import aurora
            self._aurora_available = True
            self._aurora = aurora
        except ImportError:
            print("AURORA not installed. Install with:")
            print("  pip install git+https://github.com/JackieHanLab/Aurora.git")
            self._aurora_available = False
        
        return self._aurora_available
    
    def configure_modality(
        self,
        modality_name: str,
        adata,
        sample_id: str = "sample_ID",
        labels: Optional[Dict[str, Any]] = None
    ) -> Dict:
        """
        Configure a modality dataset
        
        Args:
            modality_name: Name of modality (e.g., "transcriptome", "proteome")
            adata: AnnData object with omics data
            sample_id: Column name for unique sample ID
            labels: Dict with label columns (e.g., {"age": 65, "disease": "MASLD"})
        
        Returns:
            Configuration result
        """
        if not self._check_aurora():
            return {"status": "error", "message": "AURORA not available"}
        
        try:
            import aurora
            
            # Add input layer
            adata.layers['input'] = adata.X
            
            # Configure dataset
            aurora.configure_dataset(
                adata,
                use_layers='input',
                use_uid=sample_id,
                use_labels=list(labels.keys()) if labels else None
            )
            
            self.datasets[modality_name] = {
                "adata": adata,
                "labels": labels or {},
                "configured": True
            }
            
            return {
                "status": "success",
                "modality": modality_name,
                "samples": adata.n_obs,
                "features": adata.n_vars
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def train_model(
        self,
        features: Optional[List[str]] = None,
        project_name: str = "arp_project",
        epochs: int = 100,
        batch_size: int = 32
    ) -> Optional[Any]:
        """
        Train AURORA model on configured modalities
        
        Args:
            features: List of all feature names across modalities
            project_name: Name for saving model
            epochs: Training epochs
            batch_size: Batch size
        
        Returns:
            Trained model
        """
        if not self._check_aurora():
            return None
        
        if not self.datasets:
            print("No datasets configured. Use configure_modality() first.")
            return None
        
        try:
            import aurora
            
            # Prepare adatas dict
            adatas = {name: data["adata"] for name, data in self.datasets.items()}
            
            # Get all features if not provided
            if features is None:
                features = []
                for adata in adatas.values():
                    features.extend(adata.var_names.to_list())
            
            # Train model
            self.aurora_model = aurora.fit_model(
                adatas=adatas,
                features=features,
                project_name=project_name
            )
            
            # Save model
            model_path = self.model_dir / f"{project_name}.dill"
            self.aurora_model.save(str(model_path))
            
            return self.aurora_model
            
        except Exception as e:
            print(f"Training error: {e}")
            return None
    
    def get_embeddings(self, modality: str) -> Optional[Any]:
        """
        Get latent embeddings for a modality
        
        Args:
            modality: Modality name
        
        Returns:
            Embeddings array
        """
        if not self.aurora_model:
            print("No model trained. Use train_model() first.")
            return None
        
        try:
            adata = self.datasets.get(modality, {}).get("adata")
            if not adata:
                return None
            
            embeddings = self.aurora_model.encode_data(modality, adata)
            adata.obsm["X_latent"] = embeddings
            
            return embeddings
            
        except Exception as e:
            print(f"Embedding error: {e}")
            return None
    
    def reconstruct_modality(
        self,
        target_modality: str,
        source_modality: str
    ) -> Optional[Any]:
        """
        Reconstruct target modality from source modality embeddings
        
        Args:
            target_modality: Modality to reconstruct
            source_modality: Source modality for encoding
        
        Returns:
            Reconstructed data
        """
        if not self.aurora_model:
            print("No model trained. Use train_model() first.")
            return None
        
        try:
            source_adata = self.datasets.get(source_modality, {}).get("adata")
            target_adata = self.datasets.get(target_modality, {}).get("adata")
            
            if not source_adata or not target_adata:
                return None
            
            # Encode source
            embeddings = self.aurora_model.encode_data(source_modality, source_adata)
            
            # Decode to target
            reconstructed = self.aurora_model.decode_data(
                target_modality,
                embeddings,
                source_modality
            )
            
            return reconstructed
            
        except Exception as e:
            print(f"Reconstruction error: {e}")
            return None
    
    def predict_intervention_response(
        self,
        baseline_modality: str,
        intervention: str,
        response_modality: str = "proteome"
    ) -> Dict:
        """
        Predict response to intervention using AURORA
        
        Args:
            baseline_modality: Baseline modality data
            intervention: Intervention name (e.g., "semaglutide", "exercise")
            response_modality: Expected response modality
        
        Returns:
            Predicted response
        """
        # This would require trained model with intervention data
        return {
            "status": "experimental",
            "message": "Intervention response prediction requires training data with intervention labels",
            "suggestion": "Add intervention response labels to training data"
        }
    
    def load_model(self, model_path: str) -> bool:
        """
        Load a pre-trained AURORA model
        
        Args:
            model_path: Path to .dill model file
        
        Returns:
            True if successful
        """
        if not self._check_aurora():
            return False
        
        try:
            from aurora import load_model
            
            self.aurora_model = load_model(model_path)
            return True
            
        except Exception as e:
            print(f"Model loading error: {e}")
            return False


def quick_analysis(
    adatas: Dict[str, Any],
    project_name: str = "arp_analysis"
) -> Dict:
    """
    Quick AURORA analysis helper
    
    Usage:
        results = quick_analysis({
            "transcriptome": adata_rna,
            "proteome": adata_protein
        }, project_name="masld")
    """
    researcher = AuroraResearcher()
    
    # Configure all modalities
    for name, adata in adatas.items():
        result = researcher.configure_modality(name, adata)
        if result.get("status") == "error":
            return result
    
    # Train model
    model = researcher.train_model(project_name=project_name)
    if not model:
        return {"status": "error", "message": "Training failed"}
    
    return {
        "status": "success",
        "model": model,
        "project_name": project_name
    }


# Demo function
def demo():
    """Demo AURORA integration"""
    print("=" * 70)
    print("AURORA Integration Demo")
    print("=" * 70)
    
    researcher = AuroraResearcher()
    
    # Check if AURORA is available
    if researcher._check_aurora():
        print("✅ AURORA loaded successfully")
        print("\nWorkflow:")
        print("  1. configure_modality(name, adata)")
        print("  2. train_model(features, project_name)")
        print("  3. get_embeddings(modality)")
        print("  4. reconstruct_modality(target, source)")
    else:
        print("⚠️ AURORA not installed")
        print("\nTo install:")
        print("  pip install git+https://github.com/JackieHanLab/Aurora.git")


if __name__ == "__main__":
    demo()