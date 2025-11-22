import logging
from src.database import init_db, db_session
from src.database.models import Tenant, MonitoredGroup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_db():
    logger.info("Creating database tables...")
    init_db()
    
    # Create a default tenant for testing if none exists
    session = db_session()
    if not session.query(Tenant).first():
        logger.info("Creating default admin tenant...")
        admin = Tenant(
            telegram_user_id=0,  # Placeholder
            username="admin",
            subscription_tier="guard"
        )
        session.add(admin)
        session.commit()
        logger.info("Default tenant created.")
    else:
        logger.info("Database already initialized.")

if __name__ == "__main__":
    setup_db()
