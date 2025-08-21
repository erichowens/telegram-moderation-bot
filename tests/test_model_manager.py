"""
Integration tests for the AI model manager.
Tests model downloading, loading, and validation.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import json

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from model_manager import ModelManager


class TestModelManager:
    """Test the ModelManager functionality."""
    
    @pytest.fixture
    def temp_models_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def model_manager(self, temp_models_dir):
        """Create a ModelManager instance with temporary directory."""
        return ModelManager(models_dir=temp_models_dir)
    
    def test_model_manager_initialization(self, model_manager, temp_models_dir):
        """Test ModelManager initialization."""
        assert model_manager.models_dir == Path(temp_models_dir)
        assert model_manager.models_dir.exists()
        assert len(model_manager.available_models) > 0
        
        # Check that we have expected models
        expected_models = ["toxicity_detector", "hate_speech_detector", "spam_detector"]
        for model_name in expected_models:
            assert model_name in model_manager.available_models
    
    def test_model_info_structure(self, model_manager):
        """Test that model info has required fields."""
        for model_name, model_info in model_manager.available_models.items():
            required_fields = ["name", "description", "model_id", "task", "size_mb"]
            for field in required_fields:
                assert field in model_info, f"Model {model_name} missing field {field}"
            
            # Validate field types
            assert isinstance(model_info["size_mb"], (int, float))
            assert model_info["size_mb"] > 0
            assert isinstance(model_info["name"], str)
            assert len(model_info["name"]) > 0
    
    def test_check_models_status_empty(self, model_manager):
        """Test status check when no models are downloaded."""
        status = model_manager.check_models_status()
        
        assert "all_ready" in status
        assert "missing" in status
        assert "available" in status
        assert "details" in status
        
        assert status["all_ready"] == False
        assert len(status["missing"]) > 0
        assert len(status["available"]) == 0
    
    def test_check_models_status_with_model(self, model_manager, temp_models_dir):
        """Test status check with a mock downloaded model."""
        # Create a fake model directory
        model_path = Path(temp_models_dir) / "toxicity_detector"
        model_path.mkdir()
        
        # Create required files
        (model_path / "config.json").write_text('{"model_type": "test"}')
        (model_path / "pytorch_model.bin").write_bytes(b"fake model data")
        
        status = model_manager.check_models_status()
        
        assert "toxicity_detector" in status["available"]
        assert "toxicity_detector" not in status["missing"]
        assert status["details"]["toxicity_detector"]["status"] == "ready"
    
    def test_is_model_available(self, model_manager, temp_models_dir):
        """Test model availability checking."""
        model_path = Path(temp_models_dir) / "test_model"
        
        # Test non-existent model
        assert not model_manager._is_model_available(model_path)
        
        # Test model with missing files
        model_path.mkdir()
        assert not model_manager._is_model_available(model_path)
        
        # Test model with config but no model file
        (model_path / "config.json").write_text('{"test": true}')
        assert not model_manager._is_model_available(model_path)
        
        # Test complete model
        (model_path / "pytorch_model.bin").write_bytes(b"model data")
        assert model_manager._is_model_available(model_path)
    
    def test_get_recommended_models(self, model_manager):
        """Test model recommendations for different use cases."""
        general = model_manager.get_recommended_models("general")
        assert isinstance(general, list)
        assert len(general) > 0
        assert "toxicity_detector" in general
        
        minimal = model_manager.get_recommended_models("minimal")
        assert len(minimal) <= len(general)
        
        comprehensive = model_manager.get_recommended_models("comprehensive")
        assert len(comprehensive) >= len(general)
        
        # Test unknown use case defaults to general
        unknown = model_manager.get_recommended_models("unknown_case")
        assert unknown == general
    
    def test_get_download_size(self, model_manager):
        """Test download size calculation."""
        models = ["toxicity_detector", "spam_detector"]
        total_size = model_manager.get_download_size(models)
        
        assert isinstance(total_size, (int, float))
        assert total_size > 0
        
        # Should be sum of individual model sizes
        expected_size = sum(
            model_manager.available_models[model]["size_mb"] 
            for model in models 
            if model in model_manager.available_models
        )
        assert total_size == expected_size
        
        # Test with non-existent model
        total_with_invalid = model_manager.get_download_size(["invalid_model"])
        assert total_with_invalid == 0
    
    def test_validate_system_requirements(self, model_manager):
        """Test system requirements validation."""
        models = ["toxicity_detector"]
        requirements = model_manager.validate_system_requirements(models)
        
        required_fields = ["sufficient_space", "required_space_mb", "available_space_gb", "has_transformers", "models_supported"]
        for field in required_fields:
            assert field in requirements
        
        assert isinstance(requirements["sufficient_space"], bool)
        assert isinstance(requirements["required_space_mb"], (int, float))
        assert isinstance(requirements["available_space_gb"], (int, float))
        assert isinstance(requirements["has_transformers"], bool)
        assert requirements["models_supported"] == models
    
    def test_cleanup_models(self, model_manager, temp_models_dir):
        """Test model cleanup functionality."""
        # Create fake models
        model1_path = Path(temp_models_dir) / "model1"
        model2_path = Path(temp_models_dir) / "model2"
        
        model1_path.mkdir()
        model2_path.mkdir()
        (model1_path / "test.txt").write_text("test")
        (model2_path / "test.txt").write_text("test")
        
        # Test selective cleanup
        model_manager.cleanup_models(["model1"])
        assert not model1_path.exists()
        assert model2_path.exists()
        
        # Test full cleanup
        model_manager.cleanup_models()
        assert not model2_path.exists()
        assert model_manager.models_dir.exists()  # Directory itself should remain
    
    @patch('model_manager.HAS_TRANSFORMERS', True)
    @patch('model_manager.snapshot_download')
    def test_download_model_success(self, mock_download, model_manager, temp_models_dir):
        """Test successful model download."""
        model_name = "toxicity_detector"
        
        # Mock successful download
        def mock_download_func(repo_id, local_dir, local_dir_use_symlinks):
            # Create fake downloaded files
            local_path = Path(local_dir)
            local_path.mkdir(exist_ok=True)
            (local_path / "config.json").write_text('{"model_type": "test"}')
            (local_path / "pytorch_model.bin").write_bytes(b"fake model")
        
        mock_download.side_effect = mock_download_func
        
        result = model_manager.download_model(model_name)
        
        assert result == True
        mock_download.assert_called_once()
        
        # Verify files were created
        model_path = Path(temp_models_dir) / model_name
        assert model_path.exists()
        assert (model_path / "config.json").exists()
        assert (model_path / "pytorch_model.bin").exists()
    
    @patch('model_manager.HAS_TRANSFORMERS', True)
    @patch('model_manager.snapshot_download')
    def test_download_model_failure(self, mock_download, model_manager, temp_models_dir):
        """Test failed model download."""
        model_name = "toxicity_detector"
        
        # Mock download failure
        mock_download.side_effect = Exception("Download failed")
        
        result = model_manager.download_model(model_name)
        
        assert result == False
        
        # Verify cleanup occurred
        model_path = Path(temp_models_dir) / model_name
        assert not model_path.exists()
    
    @patch('model_manager.HAS_TRANSFORMERS', False)
    def test_download_without_transformers(self, model_manager):
        """Test download attempt without transformers library."""
        with pytest.raises(RuntimeError, match="Transformers library required"):
            model_manager.download_default_models()
    
    def test_download_unknown_model(self, model_manager):
        """Test downloading an unknown model."""
        with pytest.raises(ValueError, match="Unknown model"):
            model_manager.download_model("non_existent_model")
    
    @patch('model_manager.HAS_TRANSFORMERS', True)
    @patch('model_manager.pipeline')
    def test_load_model_success(self, mock_pipeline, model_manager, temp_models_dir):
        """Test successful model loading."""
        model_name = "toxicity_detector"
        
        # Create fake model files
        model_path = Path(temp_models_dir) / model_name
        model_path.mkdir()
        (model_path / "config.json").write_text('{"model_type": "test"}')
        (model_path / "pytorch_model.bin").write_bytes(b"fake model")
        
        # Mock pipeline creation
        mock_pipeline_instance = Mock()
        mock_pipeline.return_value = mock_pipeline_instance
        
        result = model_manager.load_model(model_name)
        
        assert result == mock_pipeline_instance
        mock_pipeline.assert_called_once()
        
        # Verify correct parameters
        call_args = mock_pipeline.call_args
        assert call_args[1]["task"] == "text-classification"
        assert str(model_path) in call_args[1]["model"]
        assert call_args[1]["device"] == -1  # CPU
    
    def test_load_model_not_available(self, model_manager):
        """Test loading a model that hasn't been downloaded."""
        with pytest.raises(FileNotFoundError, match="Model toxicity_detector not found"):
            model_manager.load_model("toxicity_detector")
    
    def test_load_unknown_model(self, model_manager):
        """Test loading an unknown model."""
        with pytest.raises(ValueError, match="Unknown model"):
            model_manager.load_model("unknown_model")
    
    @patch('model_manager.HAS_TRANSFORMERS', True)
    @patch('model_manager.snapshot_download')
    def test_update_model(self, mock_download, model_manager, temp_models_dir):
        """Test model update functionality."""
        model_name = "toxicity_detector"
        
        # Create old model
        old_model_path = Path(temp_models_dir) / model_name
        old_model_path.mkdir()
        (old_model_path / "old_file.txt").write_text("old version")
        
        # Mock download for update
        def mock_download_func(repo_id, local_dir, local_dir_use_symlinks):
            local_path = Path(local_dir)
            local_path.mkdir(exist_ok=True)
            (local_path / "config.json").write_text('{"model_type": "updated"}')
            (local_path / "pytorch_model.bin").write_bytes(b"updated model")
        
        mock_download.side_effect = mock_download_func
        
        result = model_manager.update_model(model_name)
        
        assert result == True
        
        # Verify old files are gone and new files exist
        assert not (old_model_path / "old_file.txt").exists()
        assert (old_model_path / "config.json").exists()
        assert (old_model_path / "pytorch_model.bin").exists()


class TestModelManagerEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_models_directory(self):
        """Test behavior with non-existent models directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nonexistent_dir = os.path.join(temp_dir, "nonexistent")
            manager = ModelManager(models_dir=nonexistent_dir)
            
            # Should create the directory
            assert Path(nonexistent_dir).exists()
    
    def test_invalid_model_directory_structure(self, model_manager, temp_models_dir):
        """Test handling of corrupted model directories."""
        # Create a model directory with invalid structure
        model_path = Path(temp_models_dir) / "corrupted_model"
        model_path.mkdir()
        
        # Create a file instead of expected config
        (model_path / "config.json").write_text("invalid json {")
        
        # Should handle gracefully
        assert not model_manager._is_model_available(model_path)
    
    @patch('model_manager.shutil.disk_usage')
    def test_insufficient_disk_space(self, mock_disk_usage, model_manager):
        """Test system requirements check with insufficient disk space."""
        # Mock very low disk space
        mock_disk_usage.return_value = Mock(free=1024 * 1024)  # 1MB
        
        requirements = model_manager.validate_system_requirements(["toxicity_detector"])
        
        assert requirements["sufficient_space"] == False
        assert requirements["available_space_gb"] < 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])