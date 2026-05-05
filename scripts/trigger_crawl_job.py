import json
import os
import datetime
from zoneinfo import ZoneInfo
import redis

redis_url = os.getenv("REDIS_URL", "redis://default:tcs@localhost:6379")
scheduled_crawl_job_stream_name = os.getenv("SCHEDULED_CRAWL_JOB_STREAM_NAME", "pazyr_scheduled_crawl_jobs")
if not redis_url:
    raise ValueError("REDIS_URL is not set")

if not scheduled_crawl_job_stream_name:
    raise ValueError("SCHEDULED_CRAWL_JOB_STREAM_NAME is not set")

# def build_job():
#     return {
#         "start_date": (
#             datetime.datetime.now(ZoneInfo("Asia/Kolkata"))
#             - datetime.timedelta(days=3)
#         ).isoformat()
#     }

def build_job():
    return {
        "start_date": "2026-05-04T00:00:00+00:00"  # or read from config.yaml
    }

def main():
    client = redis.Redis.from_url(redis_url, decode_responses=True)

    job = build_job()

    msg_id = client.xadd(
        scheduled_crawl_job_stream_name,
        {"data": json.dumps(job)},
        maxlen=10000,
        approximate=True
    )
    
    with open("crawl_job.log", "a", encoding="utf-8") as f:
        f.write(f"Scheduled Crawl job for {job['start_date']}, message_id - {msg_id}\n")

if __name__ == "__main__":
    main()