from src.database import db_session
from src.database.models import ViolationLog, MessageLog

class LogManager:
    @staticmethod
    def log_violation(group_id: int, user_id: int, username: str, 
                     violation_type: str, content_type: str, 
                     confidence: float, reason: str, action_taken: str):
        """Log a violation to the database."""
        session = db_session()
        try:
            log = ViolationLog(
                group_id=group_id,
                user_id=user_id,
                username=username,
                violation_type=violation_type,
                content_type=content_type,
                confidence=confidence,
                reason=reason,
                action_taken=action_taken
            )
            session.add(log)
            session.commit()
        except Exception as e:
            print(f"Failed to log violation: {e}")
        finally:
            session.close()

    @staticmethod
    def log_message(group_id: int, user_id: int, username: str, 
                   content_hash: str, message_length: int, has_link: bool):
        """Log a message metadata for analytics."""
        session = db_session()
        try:
            log = MessageLog(
                group_id=group_id,
                user_id=user_id,
                username=username,
                content_hash=content_hash,
                message_length=message_length,
                has_link=has_link
            )
            session.add(log)
            session.commit()
        except Exception as e:
            print(f"Failed to log message: {e}")
        finally:
            session.close()
