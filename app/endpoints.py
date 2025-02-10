from fastapi import APIRouter
from app.config import SNS_TOPIC_ARN
from app.services.post_processor import process_all_posts
from app.services.sns_client import subscribe_to_topic, publish_message

router = APIRouter()

@router.get("/")
async def process_posts():
    """Fetch posts, process them, and publish to SNS."""
    result = await process_all_posts(topic_arn=SNS_TOPIC_ARN)
    return result

# This endpoint is used to create a connection with the Order Processor.
@router.post("/subscribe")
async def subscribe():
    response = subscribe_to_topic(
        topic_arn=SNS_TOPIC_ARN,
        protocol="http",
        endpoint="http://order_processor:8001/sns-webhook",
    )
    return {"message": "Subscription request sent", "response": response}

# This will publish a message to the SNS topic
@router.post("/publish-message/")
async def publish_message_endpoint(message: str):
    response = publish_message(topic_arn=SNS_TOPIC_ARN, message=message)
    return {"message": "Message published", "response": response}
