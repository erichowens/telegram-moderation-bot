"""
Configuration Manager
Handles loading settings from Database with fallback to defaults.
"""
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from src.database.models import MonitoredGroup, Tenant
from src.database import db_session

logger = logging.getLogger(__name__)

class ConfigManager:
    DEFAULT_CONFIG = {
        "spam_threshold": 0.8,
        "toxicity_threshold": 0.7,
        "max_caps_ratio": 0.7,
        "enabled_features": ["spam", "toxicity", "caps"],
        "actions": {
            "spam": "delete",
            "toxicity": "warn",
            "caps": "delete"
        }
    }

    @staticmethod
    def get_group_config(group_id: int) -> Dict[str, Any]:
        """Get configuration for a specific group."""
        session = db_session()
        try:
            group = session.query(MonitoredGroup).filter_by(id=group_id).first()
            if group and group.config:
                # Merge default config with group config
                config = ConfigManager.DEFAULT_CONFIG.copy()
                config.update(group.config)
                return config
            
            return ConfigManager.DEFAULT_CONFIG
        except Exception as e:
            logger.error(f"Failed to load config for group {group_id}: {e}")
            return ConfigManager.DEFAULT_CONFIG
        finally:
            session.close()

    @staticmethod
    def get_or_create_group(group_id: int, title: str) -> MonitoredGroup:
        """Ensure group exists in DB."""
        session = db_session()
        try:
            group = session.query(MonitoredGroup).filter_by(id=group_id).first()
            if not group:
                logger.info(f"Registering new group: {title} ({group_id})")
                # Assign to default tenant (ID 1) for now
                # In production, this would require an onboarding flow
                group = MonitoredGroup(
                    id=group_id,
                    title=title,
                    tenant_id=1, 
                    config=ConfigManager.DEFAULT_CONFIG
                )
                session.add(group)
                session.commit()
            elif group.title != title:
                # Update title if changed
                group.title = title
                session.commit()
            
            return group
        except Exception as e:
            logger.error(f"Error registering group {group_id}: {e}")
            session.rollback()
            return None
        finally:
            session.close()
