"""
Model Manager - Production-ready AI model management for content moderation.
"""

import os
import requests
import zipfile
import shutil
from typing import Dict, Callable, Optional, List
from pathlib import Path
import logging
import json
import hashlib

try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
    from huggingface_hub import hf_hub_download, snapshot_download
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

logger = logging.getLogger(__name__)


class ModelManager:
    """Production AI model manager with proper validation and caching."""
    
    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        
        # Production-ready models for content moderation
        self.available_models = {
            "toxicity_detector": {
                "name": "Toxic Content Detector",
                "description": "Detects toxic, offensive, and harmful text content",
                "model_id": "unitary/toxic-bert", 
                "task": "text-classification",
                "size_mb": 420,
                "accuracy": "High",
                "speed": "Fast",
                "languages": ["en"],
                "categories": ["toxicity", "severe_toxicity", "obscene", "threat", "insult"]
            },
            "hate_speech_detector": {
                "name": "Hate Speech Classifier",
                "description": "Specialized detection of hate speech and discriminatory content",
                "model_id": "martin-ha/toxic-comment-model",
                "task": "text-classification", 
                "size_mb": 265,
                "accuracy": "High",
                "speed": "Very Fast",
                "languages": ["en"],
                "categories": ["hate_speech", "harassment"]
            },
            "spam_detector": {
                "name": "Spam Content Classifier",
                "description": "Identifies spam, promotional content, and unwanted messages",
                "model_id": "madhurjindal/autonlp-Gibberish-Detector-492513457",
                "task": "text-classification",
                "size_mb": 125,
                "accuracy": "Medium", 
                "speed": "Very Fast",
                "languages": ["en"],
                "categories": ["spam", "promotional", "gibberish"]
            },
            "nsfw_image_detector": {
                "name": "NSFW Image Classifier",
                "description": "Detects adult and inappropriate visual content",
                "model_id": "Falconsai/nsfw_image_detection",
                "task": "image-classification",
                "size_mb": 90,
                "accuracy": "High",
                "speed": "Fast", 
                "categories": ["nsfw", "suggestive", "safe"]
            }
        }
    
    def check_models_status(self) -> Dict[str, any]:
        """Check which models are available locally."""
        status = {
            "all_ready": True,
            "missing": [],
            "available": [],
            "details": {}
        }
        
        for model_name, model_info in self.available_models.items():
            model_path = self.models_dir / model_name
            is_available = self._is_model_available(model_path)
            
            if is_available:
                status["available"].append(model_name)
                status["details"][model_name] = {
                    "status": "ready",
                    "path": str(model_path),
                    "size_mb": model_info["size_mb"]
                }
            else:
                status["missing"].append(model_name)
                status["all_ready"] = False
                status["details"][model_name] = {
                    "status": "missing",
                    "required_size_mb": model_info["size_mb"]
                }
        
        return status
    
    def _is_model_available(self, model_path: Path) -> bool:
        """Check if a model is properly downloaded and available."""
        if not model_path.exists():
            return False
        
        # Check for essential files
        required_files = ["config.json"]
        model_files = list(model_path.glob("*.bin")) + list(model_path.glob("*.safetensors"))
        
        has_required_files = all((model_path / f).exists() for f in required_files)
        has_model_files = len(model_files) > 0
        
        return has_required_files and has_model_files
    
    def download_default_models(self, progress_callback: Optional[Callable] = None, models_to_download: Optional[List[str]] = None):
        """Download specified models or all available models."""
        if not HAS_TRANSFORMERS:
            logger.error("Transformers library not available. Cannot download models.")
            raise RuntimeError("Transformers library required for model downloads")
        
        if models_to_download is None:
            models_to_download = ["toxicity_detector", "spam_detector"]  # Download essential models by default
        
        total_models = len(models_to_download)
        
        for i, model_name in enumerate(models_to_download, 1):
            if model_name not in self.available_models:
                logger.warning(f"Unknown model: {model_name}")
                continue
                
            if progress_callback:
                progress_callback(f"Downloading {model_name} ({i}/{total_models})")
            
            try:
                self.download_model(model_name)
            except Exception as e:
                logger.error(f"Failed to download {model_name}: {e}")
                if progress_callback:
                    progress_callback(f"Failed to download {model_name}: {str(e)[:50]}...")
    
    def download_model(self, model_name: str) -> bool:
        """Download a specific model from HuggingFace."""
        if model_name not in self.available_models:
            raise ValueError(f"Unknown model: {model_name}")
        
        model_info = self.available_models[model_name]
        model_id = model_info["model_id"]
        local_path = self.models_dir / model_name
        
        try:
            logger.info(f"Downloading {model_info['name']} from {model_id}")
            
            # Download model using HuggingFace Hub
            snapshot_download(
                repo_id=model_id,
                local_dir=local_path,
                local_dir_use_symlinks=False
            )
            
            # Verify download
            if self._is_model_available(local_path):
                logger.info(f"Successfully downloaded {model_name}")
                return True
            else:
                logger.error(f"Download verification failed for {model_name}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to download {model_name}: {e}")
            # Clean up partial download
            if local_path.exists():
                shutil.rmtree(local_path)
            return False
    
    def load_model(self, model_name: str):
        """Load a downloaded model for inference."""
        if model_name not in self.available_models:
            raise ValueError(f"Unknown model: {model_name}")
        
        model_info = self.available_models[model_name]
        local_path = self.models_dir / model_name
        
        if not self._is_model_available(local_path):
            raise FileNotFoundError(f"Model {model_name} not found at {local_path}")
        
        try:
            # Load model using transformers pipeline
            model_pipeline = pipeline(
                task=model_info["task"],
                model=str(local_path),
                device=-1  # Use CPU
            )
            
            logger.info(f"Successfully loaded {model_name}")
            return model_pipeline
            
        except Exception as e:
            logger.error(f"Failed to load {model_name}: {e}")
            raise
    
    def get_recommended_models(self, use_case: str = "general") -> List[str]:
        """Get recommended models for different use cases."""
        recommendations = {
            "general": ["toxicity_detector", "spam_detector"],
            "strict": ["toxicity_detector", "hate_speech_detector", "spam_detector"],
            "minimal": ["toxicity_detector"],
            "comprehensive": ["toxicity_detector", "hate_speech_detector", "spam_detector", "nsfw_image_detector"]
        }
        
        return recommendations.get(use_case, recommendations["general"])
    
    def get_model_info(self, model_name: Optional[str] = None) -> Dict[str, Dict]:
        """Get information about available models."""
        if model_name:
            return self.available_models.get(model_name, {})
        return self.available_models
    
    def get_download_size(self, models: List[str]) -> int:
        """Calculate total download size for specified models in MB."""
        total_size = 0
        for model_name in models:
            if model_name in self.available_models:
                total_size += self.available_models[model_name]["size_mb"]
        return total_size
    
    def validate_system_requirements(self, models: List[str]) -> Dict[str, any]:
        """Check if system can handle the specified models."""
        total_size_mb = self.get_download_size(models)
        free_space_gb = shutil.disk_usage(self.models_dir).free // (1024 ** 3)
        
        return {
            "sufficient_space": free_space_gb * 1024 > total_size_mb * 2,  # 2x safety margin
            "required_space_mb": total_size_mb,
            "available_space_gb": free_space_gb,
            "has_transformers": HAS_TRANSFORMERS,
            "models_supported": models
        }
    
    def cleanup_models(self, models_to_remove: Optional[List[str]] = None):
        """Remove specified models or clean up corrupted downloads."""
        if models_to_remove is None:
            # Clean up all models
            if self.models_dir.exists():
                shutil.rmtree(self.models_dir)
                self.models_dir.mkdir(exist_ok=True)
            logger.info("Cleaned up all models")
        else:
            # Remove specific models
            for model_name in models_to_remove:
                model_path = self.models_dir / model_name
                if model_path.exists():
                    shutil.rmtree(model_path)
                    logger.info(f"Removed model: {model_name}")
    
    def update_model(self, model_name: str) -> bool:
        """Update a specific model to the latest version."""
        # Remove old version
        self.cleanup_models([model_name])
        
        # Download new version
        return self.download_model(model_name)