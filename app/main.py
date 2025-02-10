import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.config import SNS_TOPIC_NAME 
from app.services.sns_client import create_topic
from app.endpoints import router as api_router
from app.services.redis_manager import set_last_processed_page, set_last_processed_post

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Redis checkpoints
    set_last_processed_page(1)
    set_last_processed_post(-1)

    # Create the SNS topic
    try:
        topic_arn = create_topic(SNS_TOPIC_NAME)
        logging.info(f"SNS topic created with ARN: {topic_arn}")
    except Exception as e:
        logging.error(f"Failed to create SNS topic: {e}")

    yield

app = FastAPI(lifespan=lifespan,title="Order Fetcher", description="This is the main application for fetching posts and publishing to SNS.",version="1.0.0")
app.include_router(api_router)
