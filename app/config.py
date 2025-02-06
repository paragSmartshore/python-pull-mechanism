import os

LOCALSTACK_ENDPOINT = os.getenv("LOCALSTACK_ENDPOINT", "http://localstack:4566")
SNS_TOPIC_NAME = os.getenv("SNS_TOPIC_NAME", "MyTestTopic")
SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN", f"arn:aws:sns:us-east-1:000000000000:{SNS_TOPIC_NAME}")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))

# Dummy AWS credentials for local development with LocalStack
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "test")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "test")