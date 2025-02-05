from fastapi import FastAPI
import boto3
import httpx
import redis
import logging
import asyncio

from failure_emulation import FailureEmulator

logging.basicConfig(level=logging.INFO)

app = FastAPI()
# LocalStack endpoint for AWS services
LOCALSTACK_ENDPOINT = "http://localstack:4566"
SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:000000000000:MyTestTopic"

# Redis connection for checkpoint (using the Docker Compose service name)
r = redis.StrictRedis(host="redis", port=6379, db=0, decode_responses=True)

# Initialize the boto3 SNS client (configured to use LocalStack)
sns_client = boto3.client(
    "sns",
    region_name="us-east-1",
    endpoint_url=LOCALSTACK_ENDPOINT,
)

# Configuration for retries
MAX_RETRIES = 3

# Utility functions to work with the checkpoint
def get_last_processed_page():
    return r.get("last_processed_page")

def set_last_processed_page(page: int):
    r.set("last_processed_page", page)

def get_last_processed_post():
    return r.get("last_processed_post_index")

def set_last_processed_post(index: int):
    r.set("last_processed_post_index", index)

# Reset checkpoint on startup (Issue 1)
@app.on_event("startup")
async def startup_event():
    set_last_processed_page(1)
    set_last_processed_post(-1)
    logging.info("Checkpoints reset on startup.")

# Helper function to fetch posts for a given page
async def fetch_posts(page: int):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://jsonplaceholder.typicode.com/posts?_page={page}&_limit=10"
        )
        return response.json()

async def process_post(post, current_page: int, post_index: int, failure_emulator: FailureEmulator):
    # Simulate failure for specific post
    failure_emulator.check_failure(current_page, post_index)
    
    # Process the post (you can add more processing logic here)
    return post

# Automatically process all pages until no more data is returned (Issue 2)
@app.get("/")
async def process_all_posts():
    failure_emulator = FailureEmulator(MAX_RETRIES)
    combined_posts = []
    page_retries = 0
    post_retries = 0  # New counter specifically for post retries

    while True:
        last_page = get_last_processed_page()
        current_page = int(last_page) if last_page is not None else 1
        logging.info(f"Fetching page {current_page}")
        
        try:
            posts = await fetch_posts(current_page)
            if not posts:
                logging.info("No more posts found; finishing processing.")
                break

            last_post_index = int(get_last_processed_post() or -1)
            
            i = last_post_index + 1
            while i < len(posts):
                try:
                    processed_post = await process_post(posts[i], current_page, i, failure_emulator)
                    combined_posts.append(processed_post)
                    set_last_processed_post(i)
                    post_retries = 0  # Reset post retries after successful processing
                    i += 1
                except Exception as e:
                    logging.error(f"Error processing post {i} on page {current_page}: {e}")
                    if post_retries < MAX_RETRIES:
                        post_retries += 1
                        logging.info(f"Retrying post {i} on page {current_page} (attempt {post_retries}/{MAX_RETRIES})...")
                        await asyncio.sleep(1)
                        continue  # Retry the same post without incrementing i
                    else:
                        logging.error(f"Max retries exceeded for post {i} on page {current_page}. Aborting process.")
                        raise Exception(f"Max retries exceeded for post {i} on page {current_page}") from e

            # Reset post index and move to next page
            set_last_processed_post(-1)
            set_last_processed_page(current_page + 1)
            page_retries = 0
            post_retries = 0
            
            await asyncio.sleep(0.1)

        except Exception as e:
            logging.error(f"Error processing page {current_page}: {e}")
            if page_retries < MAX_RETRIES:
                page_retries += 1
                logging.info(f"Retrying page {current_page} (attempt {page_retries}/{MAX_RETRIES})...")
                # Wait a bit before retrying to allow any transient issue to resolve
                await asyncio.sleep(1)
                continue  # Do not update checkpoint so we will retry the same page
            else:
                logging.error(f"Max retries exceeded for page {current_page}. Aborting process.")
                raise Exception(f"Max retries exceeded for page {current_page}") from e

    return {"data": combined_posts, "message": "All posts have been fetched."}

# Subscribe to SNS Topic
@app.post("/subscribe")
async def subscribe():
    response = sns_client.subscribe(
        TopicArn=SNS_TOPIC_ARN,
        Protocol="http",
        Endpoint="http://host.docker.internal:8000/sns-webhook"
    )
    return {"message": "Subscription request sent", "response": response}

# Publish a message to SNS
@app.post("/publish-message/")
async def publish_message(message: str):
    response = sns_client.publish(
        TopicArn=SNS_TOPIC_ARN,
        Message=message
    )
    return {"message": "Message published", "response": response}



