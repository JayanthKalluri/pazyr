# src/discovery_engine/constants.py

DEFAULT_TIMEOUT = 5
DEFAULT_STREAM_MAX_LEN = 1000
DEFAULT_GROUP_NAME = "coe"

# Redis stream names
SCHEDULED_CRAWL_STREAM = "scheduled_crawl_jobs"
DOWNLOADER_STREAM = "downloader_jobs"
DEAD_LETTER_STREAM = "dead_letter_queue"
PROCESSING_STREAM = "processing_jobs"