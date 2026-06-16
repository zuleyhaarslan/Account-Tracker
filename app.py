import asyncio
import logging
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI

from database.connection import engine, Base
from web.routes import router as web_router
from engine.scheduler import scheduler_loop

# Initialize log format layout configurations
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ApplicationRuntime")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the application lifecycle events.
    Boots the database engine and spawns the background worker engine.
    """
    logger.info("Starting local application infrastructure nodes...")
    
    # 1. Initialize relational database tables on-disk if absent
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("SQLite database validation completed. Schema is current.")
    except Exception as e:
        logger.critical(f"Database initialization aborted due to constraint fault: {str(e)}")
        raise e

    # 2. Spawn the automated update checking engine on a background task loop
    bg_scheduler_task = asyncio.create_task(scheduler_loop())
    logger.info("Background scraping worker task successfully registered into event loop.")
    
    yield  # The web application serves local connections here...
    
    # 3. Graceful termination cleanup steps upon local process teardown
    logger.info("Shutdown signal intercepted. Terminating background workers...")
    bg_scheduler_task.cancel()
    try:
        await bg_scheduler_task
    except asyncio.CancelledError:
        logger.info("Background thread tasks drained and cleared safely.")
    logger.info("Application context closed down cleanly.")

# Instantiate core framework runtime orchestrator
app = FastAPI(
    title="Local Multi-Account Update Tracker",
    description="A sovereign local ecosystem for identity state verification.",
    lifespan=lifespan
)

# Bind presentation routes and navigation paths
app.include_router(web_router)