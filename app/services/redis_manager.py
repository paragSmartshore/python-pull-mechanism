import redis
from app.config import REDIS_HOST, REDIS_PORT

r = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

def get_last_processed_page():
    return r.get("last_processed_page")

def set_last_processed_page(page: int):
    r.set("last_processed_page", page)

def get_last_processed_post():
    return r.get("last_processed_post_index")

def set_last_processed_post(index: int):
    r.set("last_processed_post_index", index)
