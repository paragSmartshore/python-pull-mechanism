import logging
import json
import httpx
from fastapi import FastAPI, Request, HTTPException

app = FastAPI(title="Order Processor", description="API for processing SNS notifications and handling orders.",version="1.0.0")
processed_posts = []

@app.post("/sns-webhook")
async def sns_webhook(request: Request):
    payload = await request.json()
    logging.info(f"Received SNS message: {payload}")
    message_type = request.headers.get("x-amz-sns-message-type")

    if message_type == "SubscriptionConfirmation":
        subscribe_url = payload.get("SubscribeURL")
        if subscribe_url:
            if "localhost.localstack.cloud" in subscribe_url:
                subscribe_url = subscribe_url.replace("localhost.localstack.cloud", "localstack")
            logging.info(f"Confirming subscription via URL: {subscribe_url}")
            async with httpx.AsyncClient() as client:
                response = await client.get(subscribe_url)
                logging.info(f"Subscription confirmed: {response.text}")
        else:
            logging.error("No SubscribeURL in subscription confirmation payload")
    elif message_type == "Notification":
        message_str = payload.get("Message")
        try:
            message = json.loads(message_str)
        except json.JSONDecodeError:
            message = message_str
        processed_posts.append(message)
        logging.info(f"Processed posts count: {len(processed_posts)}")
    else:
        logging.error(f"Unknown SNS message type: {message_type}")
        raise HTTPException(status_code=400, detail="Unknown SNS message type")
    
    return {"status": "success"}


# This will return the processed posts from the 'app' container throught the sns-webhook endpoint
@app.get("/orders")
async def get_processed_posts():
    return {"processed_posts": processed_posts}
