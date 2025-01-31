from fastapi import FastAPI 
import boto3
import httpx

app = FastAPI()

# LocalStack endpoint for AWS services
LOCALSTACK_ENDPOINT = "http://localstack:4566"
SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:000000000000:MyTestTopic"

# Initialize the boto3 SNS client (configured to use LocalStack)
sns_client = boto3.client(
    "sns",
    region_name="us-east-1",
    endpoint_url=LOCALSTACK_ENDPOINT,  # Points to LocalStack
)


@app.get("/")
async def get_posts():
        async with httpx.AsyncClient() as client:
            response = await client.get("https://jsonplaceholder.typicode.com/posts?_page=1&_limit=10")
            return response.json()


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


