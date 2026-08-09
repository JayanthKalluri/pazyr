import datetime
import json
import os
from zoneinfo import ZoneInfo

import redis

redis_url = os.getenv("REDIS_URL", "redis://redis:redis@localhost:6379")
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
        "start_date": "2026-05-05T00:00:00+00:00"  # or read from config.yaml
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

def get_info():
    client = redis.Redis.from_url(redis_url, decode_responses=True)


    import pprint
    print("pazyr_scheduled_crawl_jobs stream info")
    crawl_job_stream_info = client.xinfo_stream(name="pazyr_scheduled_crawl_jobs")
    pprint.pprint(crawl_job_stream_info)
    print("-------------")
    print("pazyr_processing_jobs stream info")
    processing_stream_info = client.xinfo_stream(name="pazyr_processing_jobs")
    pprint.pprint(processing_stream_info)
    print("-------------")
    print("pazyr_scheduled_crawl_jobs stream groups")
    crawl_job_stream_groups = client.xinfo_groups(name="pazyr_scheduled_crawl_jobs")
    pprint.pprint(crawl_job_stream_groups)
    print("-------------")
    print("pazyr_processing_jobs stream groups")
    processing_job_stream_groups = client.xinfo_groups(name="pazyr_processing_jobs")
    pprint.pprint(processing_job_stream_groups)
    print("-------------")
    print("pazyr_scheduled_crawl_jobs stream group consumers")
    crawl_job_stream_group_consumers = client.xinfo_consumers(name="pazyr_scheduled_crawl_jobs", groupname="pazyr_discovery_workers")
    pprint.pprint(crawl_job_stream_group_consumers)
    print("-------------")
    print("pazyr_processing_jobs stream group consumers")
    processing_job_stream_group_consumers = client.xinfo_consumers(name="pazyr_processing_jobs", groupname="pazyr_analyser_workers")
    pprint.pprint(processing_job_stream_group_consumers)
    print("-------------")


def read():
    client = redis.Redis.from_url(redis_url, decode_responses=True)

    response = client.xreadgroup(
        groupname="coe",
        consumername="debug",
        streams={
            "pazyr_scheduled_crawl_jobs": ">"
        },
        count=1,
        block=1000,
    )
    print(response)

if __name__ == "__main__":
    main()
    # get_info()
    # read()