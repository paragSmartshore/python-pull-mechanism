from fastapi import FastAPI
import httpx
import boto3
import os

app = FastAPI()


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

