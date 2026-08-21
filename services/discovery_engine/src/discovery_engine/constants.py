# src/discovery_engine/constants.py

DEFAULT_TIMEOUT = 5
DEFAULT_STREAM_MAX_LEN = 1000

# Redis stream names
# SCHEDULED_CRAWL_STREAM = "scheduled_crawl_jobs"
# DOWNLOADER_STREAM = "downloader_jobs"
# PROCESSING_STREAM = "processing_jobs"
REDIS_SCHEDULED_CRAWL_JOB_STREAM_NAME="pazyr_scheduled_crawl_jobs"
REDIS_PROCESSING_STREAM_NAME="pazyr_processing_jobs"
REDIS_DEAD_LETTER_STREAM_NAME = "pazyr_dead_letter_stream"
REDIS_DISCOVERY_GROUP_NAME = "pazyr_discovery_workers"
REDIS_DISCOVERY_CONSUMER_PREFIX = "pazyr_discovery_"
