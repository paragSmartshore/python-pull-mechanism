from fastapi import FastAPI 
import boto3
import httpx
import redis
import logging

app = FastAPI()

# LocalStack endpoint for AWS services
LOCALSTACK_ENDPOINT = "http://localstack:4566"
SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:000000000000:MyTestTopic"


# Redis connection for checkpoint
r = redis.StrictRedis(host="redis", port=6379, db=0, decode_responses=True)

# Initialize the boto3 SNS client (configured to use LocalStack)
sns_client = boto3.client(
    "sns",
    region_name="us-east-1",
    endpoint_url=LOCALSTACK_ENDPOINT,  # Points to LocalStack
)


# Fetch the last processed page number from Redis (checkpoint mechanism)
def get_last_processed_page():
    return r.get("last_processed_page")

# Save the last processed page number to Redis
def set_last_processed_page(page: int):
    r.set("last_processed_page", page)


@app.get("/")
async def get_posts():
    # Check the last processed page from Redis (checkpoint)
    last_page = get_last_processed_page()
    print(last_page)
    if last_page is None:
        last_page = 1
        logging.warning(last_page)
    else:
        last_page = int(last_page)

    # Use the last processed page to fetch posts
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://jsonplaceholder.typicode.com/posts?_page={last_page}&_limit=10")
        posts = response.json()

        # After successful fetch, update the last processed page in Redis
        if posts:
            set_last_processed_page(last_page + 1)  # Increment the page number

        return posts


# **Subscribe to SNS Topic**
@app.post("/subscribe")
async def subscribe():
    response = sns_client.subscribe(
        TopicArn=SNS_TOPIC_ARN,
        Protocol="http",
        Endpoint="http://host.docker.internal:8000/sns-webhook"
    )
    return {"message": "Subscription request sent", "response": response}

#  **Publish a message to SNS**
@app.post("/publish-message/")
async def publish_message(message: str):
    response = sns_client.publish(
        TopicArn=SNS_TOPIC_ARN,
        Message=message
    )
    return {"message": "Message published", "response": response}


