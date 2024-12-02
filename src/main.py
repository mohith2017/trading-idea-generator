from fastapi import FastAPI
from .api.router import router
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from .utils.data_processing import extract_data_from_json
from .utils.create_vector_embeddings import create_vector_embeddings_data
from contextlib import asynccontextmanager
from fastapi import FastAPI
from .utils.logger_config import logger
import logging

# Configure logger
logger = logger(__name__, 'app.log', level=logging.DEBUG)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages application lifecycle events"""
    logger.info("Starting application lifespan")
    try:
        scheduler = AsyncIOScheduler()
        
        # Schedule initial data extraction job
        first_job = scheduler.add_job(extract_data_from_json)

        def schedule_vector_embeddings(event):
            """Schedule vector embeddings creation after successful data extraction"""
            if event.job_id == first_job.id and event.code == EVENT_JOB_EXECUTED:
                try:
                    scheduler.add_job(create_vector_embeddings_data)
                except Exception as e:
                    logger.error(f"Failed to schedule vector embeddings job: {str(e)}")
    
        scheduler.add_listener(schedule_vector_embeddings, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        scheduler.start()
        logger.info("Scheduler started successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Error in application lifespan: {str(e)}")
        raise
    finally:
        logger.info("Shutting down scheduler")
        scheduler.shutdown()

# Initialize FastAPI application
app = FastAPI(
    title="Trading Idea Generator",
    description="API for generating trading ideas based on market data",
    version="1.0.0",
    lifespan=lifespan
)

# Include API routes
app.include_router(router, prefix="/api")

@app.get("/", tags=["Root"])
async def read_root():
    """Root endpoint returning welcome message"""
    return {
        "message": "Welcome to Trading Idea Generator!",
        "status": "healthy"
    }
