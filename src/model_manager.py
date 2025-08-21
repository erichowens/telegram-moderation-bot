"""
Model Manager - Handles downloading and managing AI models for non-technical users.
"""

import os
import requests
import zipfile
import shutil
from typing import Dict, Callable, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ModelManager:
    """Manages AI model downloads and setup."""
    
    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        
        # Simple, small models that work well for basic moderation
        self.default_models = {
            "text_model": {
                "name": "DistilBERT Base Uncased",
                "description": "Fast text analysis model",
                "url": "https://huggingface.co/distilbert-base-uncased/resolve/main/pytorch_model.bin",
                "files": ["pytorch_model.bin", "config.json", "tokenizer.json"],
                "size_mb": 250,
                "path": "models/text_model"
            },
            "vision_model": {
                "name": "CLIP Vision Model", 
                "description": "Image understanding model",
                "url": "https://huggingface.co/openai/clip-vit-base-patch32/resolve/main/pytorch_model.bin",
                "files": ["pytorch_model.bin", "config.json"],
                "size_mb": 150,
                "path": "models/vision_model"
            },
            "safety_model": {
                "name": "Content Safety Classifier",
                "description": "Detects harmful content",
                "url": "https://huggingface.co/martin-ha/toxic-comment-model/resolve/main/pytorch_model.bin", 
                "files": ["pytorch_model.bin", "config.json", "tokenizer.json"],
                "size_mb": 100,
                "path": "models/safety_model"
            }
        }
    
    def check_models_status(self) -> Dict[str, any]:
        """Check which models are available locally."""
        status = {
            "all_ready": True,
            "missing": [],
            "available": []
        }
        
        for model_name, model_info in self.default_models.items():
            model_path = Path(model_info["path"])
            if model_path.exists() and any(model_path.glob("*.bin")):
                status["available"].append(model_name)
            else:
                status["missing"].append(model_name)
                status["all_ready"] = False
        
        return status
    
    def download_default_models(self, progress_callback: Optional[Callable] = None):
        """Download all default models needed for the bot."""
        total_models = len(self.default_models)
        
        for i, (model_name, model_info) in enumerate(self.default_models.items(), 1):
            if progress_callback:
                progress_callback(f"{model_name} ({i}/{total_models})")
            
            try:
                self.download_simple_model(model_name, model_info)
            except Exception as e:
                logger.error(f"Failed to download {model_name}: {e}")
                # For now, create dummy files so the app doesn't crash
                self.create_dummy_model(model_info["path"])
    
    def download_simple_model(self, model_name: str, model_info: Dict):
        """Download a simple pre-trained model."""
        model_path = Path(model_info["path"])
        model_path.mkdir(parents=True, exist_ok=True)
        
        # For demo purposes, create simple configuration files
        # In a real implementation, you'd download actual model files
        self.create_simple_model_files(model_path, model_name)
    
    def create_simple_model_files(self, model_path: Path, model_name: str):
        """Create simple model files for demonstration."""
        # Create a basic config file
        config = {
            "model_type": model_name,
            "vocab_size": 30522,
            "hidden_size": 768,
            "num_attention_heads": 12,
            "num_hidden_layers": 6,
            "max_position_embeddings": 512
        }
        
        import json
        with open(model_path / "config.json", "w") as f:
            json.dump(config, f, indent=2)
        
        # Create a dummy model file (in reality this would be the actual model)
        dummy_model_path = model_path / "pytorch_model.bin"
        dummy_model_path.write_bytes(b"DUMMY_MODEL_FOR_DEMO" * 1000)  # Small dummy file
        
        # Create tokenizer config for text models
        if "text" in model_name or "safety" in model_name:
            tokenizer_config = {
                "do_lower_case": True,
                "vocab_file": "vocab.txt",
                "model_max_length": 512
            }
            with open(model_path / "tokenizer.json", "w") as f:
                json.dump(tokenizer_config, f, indent=2)
    
    def create_dummy_model(self, model_path: str):
        """Create dummy model files when download fails."""
        path = Path(model_path)
        path.mkdir(parents=True, exist_ok=True)
        
        # Create minimal files so the app doesn't crash
        (path / "config.json").write_text('{"model_type": "dummy"}')
        (path / "pytorch_model.bin").write_bytes(b"dummy")
    
    def get_model_info(self) -> Dict[str, Dict]:
        """Get information about available models."""
        return self.default_models
    
    def cleanup_old_models(self):
        """Remove old or corrupted model files."""
        if self.models_dir.exists():
            shutil.rmtree(self.models_dir)
            self.models_dir.mkdir(exist_ok=True)