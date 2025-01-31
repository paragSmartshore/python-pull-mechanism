from fastapi import FastAPI
import httpx
import boto3
import os

app = FastAPI()


# SNS Configuration (LocalStack)
SNS_ENDPOINT = os.getenv("SNS_ENDPOINT", "http://localhost:4566")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "test")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "test")

sns_client = boto3.client(
    "sns",
    region_name=AWS_REGION,
    endpoint_url=SNS_ENDPOINT,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)


TOPIC_ARN = None  # This will be created dynamically


@app.on_event("startup")
async def startup_event():
    """Create an SNS topic when the app starts."""
    global TOPIC_ARN
    response = sns_client.create_topic(Name="MyTestTopic")
    TOPIC_ARN = response["TopicArn"]


@app.get("/")
async def root():
    return {"message": "Hello, FastAPI in Docker!"}


@app.get("/test")
async def root():
    return {"message": "test route"}

@app.get("/get-posts")
async def get_posts():
        async with httpx.AsyncClient() as client:
            response = await client.get("https://jsonplaceholder.typicode.com/posts?_page=1&_limit=2")
            return response.json()


@app.post("/publish-message/")
async def publish_message(message: str):
    """Publish a message to the SNS topic."""
    response = sns_client.publish(
        TopicArn=TOPIC_ARN,
        Message=message,
        Subject="Test Notification"
    )
    return {"MessageId": response["MessageId"]}

