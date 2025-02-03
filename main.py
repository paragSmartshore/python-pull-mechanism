import random
from fastapi import FastAPI
import boto3
import httpx
import redis
import logging
import asyncio

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

# Configuration for failure simulation and retries
SIMULATE_FAILURE_ON_PAGE = 3  # Emulate failure on page 3 once
MAX_RETRIES = 3
failure_simulated = False  # Global flag to only simulate the error once

# Utility functions to work with the checkpoint
def get_last_processed_page():
    return r.get("last_processed_page")

def set_last_processed_page(page: int):
    r.set("last_processed_page", page)

# Reset checkpoint on startup (Issue 1)
@app.on_event("startup")
async def startup_event():
    # Either flush the entire Redis DB:
    # r.flushdb()
    # Or simply set the starting page to 1:
    set_last_processed_page(1)
    logging.info("Checkpoint reset to 1 on startup.")

# Helper function to fetch posts for a given page
async def fetch_posts(page: int):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://jsonplaceholder.typicode.com/posts?_page={page}&_limit=10"
        )
        # You could add error handling here if needed
        return response.json()

# Automatically process all pages until no more data is returned (Issue 2)
@app.get("/")
async def process_all_posts():
    # Set up random failure simulation: choose a random page (from 2 to 10) 
    # and a random number of failures (between 1 and MAX_RETRIES-1) before succeeding.
    simulate_failure_page = random.randint(2, 10)
    simulate_failure_attempts_required = random.randint(1, MAX_RETRIES - 1) if MAX_RETRIES > 1 else 0
    simulate_failures_done = 0
    logging.info(
        f"Simulated failure will occur on page {simulate_failure_page} "
        f"and require {simulate_failure_attempts_required} failure(s) before succeeding."
    )

    combined_posts = []
    retries = 0

    while True:
        # Get the current page from checkpoint (default to 1 if not set)
        last_page = get_last_processed_page()
        current_page = int(last_page) if last_page is not None else 1
        logging.info(f"Fetching page {current_page}")
        
        try:
            # Trigger simulated failure on the designated random page until it has failed
            # the required number of times.
            if current_page == simulate_failure_page and simulate_failures_done < simulate_failure_attempts_required:
                simulate_failures_done += 1
                raise Exception(
                    f"Simulated failure on page {current_page} "
                    f"(attempt {simulate_failures_done} of {simulate_failure_attempts_required})"
                )
            
            posts = await fetch_posts(current_page)
            # If no posts are returned, we have reached the end of available data
            if not posts:
                logging.info("No more posts found; finishing processing.")
                break

            combined_posts.extend(posts)
            # Only update the checkpoint after a successful call
            set_last_processed_page(current_page + 1)
            # Reset retry count for next page on successful fetch
            retries = 0

            # Small delay between requests to avoid overloading the API
            await asyncio.sleep(0.1)

        except Exception as e:
            logging.error(f"Error processing page {current_page}: {e}")
            if retries < MAX_RETRIES:
                retries += 1
                logging.info(f"Retrying page {current_page} (attempt {retries}/{MAX_RETRIES})...")
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



