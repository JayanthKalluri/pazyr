# src/discovery_engine/constants.py

DEFAULT_TIMEOUT = 5
DEFAULT_STREAM_MAX_LEN = 1000

# Redis stream names
# SCHEDULED_CRAWL_STREAM = "scheduled_crawl_jobs"
# DOWNLOADER_STREAM = "downloader_jobs"
# PROCESSING_STREAM = "processing_jobs"
DEAD_LETTER_STREAM = "pazyr_dead_letter_stream"
DISCOVERY_GROUP_NAME = "pazyr_discovery_workers"
ANALYSER_GROUP_NAME = "pazyr_analyser_workers"
DISCOVERY_CONSUMER_PREFIX = "pazyr_discovery_"
ANALYSER_CONSUMER_PREFIX = "pazyr_analyser_"