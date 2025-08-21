"""
Configuration management for the Telegram moderation bot.
"""

import yaml
import os
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class PolicyConfig:
    """Configuration for a moderation policy."""
    name: str
    description: str
    threshold: float
    action: str


@dataclass
class ModelConfig:
    """Configuration for a model."""
    type: str
    path: str


class Config:
    """Main configuration class."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = config_path
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    @property
    def telegram_token(self) -> str:
        """Get Telegram bot token."""
        return self._config['telegram']['token']
    
    @property
    def allowed_chats(self) -> List[int]:
        """Get list of allowed chat IDs."""
        return self._config['telegram'].get('allowed_chats', [])
    
    @property
    def text_model(self) -> ModelConfig:
        """Get text model configuration."""
        model_config = self._config['moderation']['text_model']
        return ModelConfig(
            type=model_config['type'],
            path=model_config['path']
        )
    
    @property
    def vision_model(self) -> ModelConfig:
        """Get vision model configuration."""
        model_config = self._config['moderation']['vision_model']
        return ModelConfig(
            type=model_config['type'],
            path=model_config['path']
        )
    
    @property
    def multimodal_model(self) -> ModelConfig:
        """Get multimodal model configuration."""
        model_config = self._config['moderation']['multimodal_model']
        return ModelConfig(
            type=model_config['type'],
            path=model_config['path']
        )
    
    @property
    def policies(self) -> List[PolicyConfig]:
        """Get list of moderation policies."""
        policies = []
        for policy_data in self._config['policies']:
            policies.append(PolicyConfig(
                name=policy_data['name'],
                description=policy_data['description'],
                threshold=policy_data['threshold'],
                action=policy_data['action']
            ))
        return policies
    
    @property
    def log_level(self) -> str:
        """Get logging level."""
        return self._config.get('logging', {}).get('level', 'INFO')
    
    @property
    def log_file(self) -> str:
        """Get log file path."""
        return self._config.get('logging', {}).get('file', 'logs/bot.log')
    
    @property
    def max_concurrent_requests(self) -> int:
        """Get maximum concurrent requests."""
        return self._config.get('performance', {}).get('max_concurrent_requests', 10)
    
    @property
    def request_timeout(self) -> int:
        """Get request timeout in seconds."""
        return self._config.get('performance', {}).get('request_timeout', 30)