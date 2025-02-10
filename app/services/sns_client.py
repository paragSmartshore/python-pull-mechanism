import boto3
import logging
from app.config import LOCALSTACK_ENDPOINT, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

# Initialize the boto3 SNS client (configured to use LocalStack)
sns_client = boto3.client(
    "sns",
    region_name="us-east-1",
    endpoint_url=LOCALSTACK_ENDPOINT,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

def create_topic(topic_name: str) -> str:
    try:
        response = sns_client.create_topic(Name=topic_name)
        topic_arn = response["TopicArn"]
        logging.info(f"SNS topic created with ARN: {topic_arn}")
        return topic_arn
    except Exception as e:
        logging.error(f"Failed to create SNS topic: {e}")
        raise

def publish_message(topic_arn: str, message: str):
    try:
        response = sns_client.publish(TopicArn=topic_arn, Message=message)
        logging.info(f"Published message to {topic_arn}")
        return response
    except Exception as e:
        logging.error(f"Failed to publish message: {e}")
        raise

def subscribe_to_topic(topic_arn: str, protocol: str, endpoint: str):
    try:
        response = sns_client.subscribe(
            TopicArn=topic_arn,
            Protocol=protocol,
            Endpoint=endpoint
        )
        logging.info("Subscription request sent")
        return response
    except Exception as e:
        logging.error(f"Failed to subscribe: {e}")
        raise
