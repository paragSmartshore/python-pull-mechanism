import json
import asyncio
import logging
import httpx

from app.config import MAX_RETRIES
from app.services.redis_manager import (
    get_last_processed_page,
    set_last_processed_page,
    get_last_processed_post,
    set_last_processed_post,
)
from app.services.sns_client import publish_message
from app.services.failure_emulator import FailureEmulator  

async def fetch_posts(page: int):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://jsonplaceholder.typicode.com/posts?_page={page}&_limit=10"
        )
        return response.json()

async def process_post(post, current_page: int, post_index: int, failure_emulator: FailureEmulator):
    # This will raise an exception if a simulated failure occurs.
    failure_emulator.check_failure(current_page, post_index)
    return post

async def process_all_posts(topic_arn: str):
    failure_emulator = FailureEmulator(MAX_RETRIES)
    combined_posts = []
    page_retries = 0
    post_retries = 0

    while True:
        last_page = get_last_processed_page()
        current_page = int(last_page) if last_page is not None else 1
        logging.info(f"Fetching page {current_page}")

        try:
            posts = await fetch_posts(current_page)
            if not posts:
                logging.info("No more posts found. Finishing processing.")
                break

            last_post_index = int(get_last_processed_post() or -1)
            i = last_post_index + 1

            while i < len(posts):
                try:
                    processed_post = await process_post(posts[i], current_page, i, failure_emulator)
                    combined_posts.append(processed_post)
                    message_str = json.dumps(processed_post)
                    publish_message(topic_arn=topic_arn, message=message_str)
                    logging.info(f"Published post {i} on page {current_page} to SNS")

                    set_last_processed_post(i)
                    post_retries = 0  # Reset post retries after a successful attempt
                    i += 1
                except Exception as e:
                    logging.error(f"Error processing post {i} on page {current_page}: {e}")
                    if post_retries < MAX_RETRIES:
                        post_retries += 1
                        logging.info(
                            f"Retrying post {i} on page {current_page} (attempt {post_retries}/{MAX_RETRIES})..."
                        )
                        await asyncio.sleep(1)
                        continue  # Retry the same post
                    else:
                        logging.error(
                            f"Max retries exceeded for post {i} on page {current_page}. Aborting process."
                        )
                        raise Exception(f"Max retries exceeded for post {i} on page {current_page}") from e

            # Reset post index and move to the next page
            set_last_processed_post(-1)
            set_last_processed_page(current_page + 1)
            page_retries = 0
            post_retries = 0
            await asyncio.sleep(0.1)

        except Exception as e:
            logging.error(f"Error processing page {current_page}: {e}")
            if page_retries < MAX_RETRIES:
                page_retries += 1
                logging.info(
                    f"Retrying page {current_page} (attempt {page_retries}/{MAX_RETRIES})..."
                )
                await asyncio.sleep(1)
                continue  # Retry the same page
            else:
                logging.error(
                    f"Max retries exceeded for page {current_page}. Aborting process."
                )
                raise Exception(f"Max retries exceeded for page {current_page}") from e

    return {"data": combined_posts, "message": "All posts have been fetched and published to SNS."}
