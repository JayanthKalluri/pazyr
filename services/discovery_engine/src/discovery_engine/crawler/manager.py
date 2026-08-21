import asyncio
import json
import socket

from pazyr_core.clients.redis_client import RedisClient
from pazyr_core.logging.logger import get_logger
from pazyr_core.types import ScheduledCrawlJob

from discovery_engine.constants import *
from discovery_engine.config import config
from discovery_engine.crawler.arxiv import crawl_arxiv

logger = get_logger(__name__)
crawler_semaphore = asyncio.Semaphore(50)


def start_crawlers(shutdown_event, create_task_fn):
    return [create_task_fn(crawler_listener(shutdown_event, create_task_fn))]


async def crawler_listener(shutdown_event, create_task_fn):
    while not shutdown_event.is_set():
        result = await pull_crawler_job()

        if not result:
            await asyncio.sleep(0.1)
            continue

        msg_id, job = result
        create_task_fn(process_job(msg_id, job, config, shutdown_event))


async def process_job(msg_id: str, job: ScheduledCrawlJob, config, shutdown_event):
    redis_client = RedisClient.get(name=config.service_name)

    if shutdown_event.is_set():
        return

    try:
        await handle_crawler_job(job, shutdown_event)
        await redis_client.ack(REDIS_SCHEDULED_CRAWL_JOB_STREAM_NAME, msg_id)
    except Exception as e:
        logger.error(f"Error occurred while processing job: {e!s}")


async def handle_crawler_job(job: ScheduledCrawlJob, shutdown_event):
    if shutdown_event.is_set():
        return

    topics, start_date = config.topics, job.start_date

    tasks = [crawl_arxiv(topics, start_date, crawler_semaphore)]

    results = await asyncio.gather(*tasks, return_exceptions=True)
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Crawler task failed: {result}", exc_info=result)


async def pull_crawler_job() -> tuple[str, ScheduledCrawlJob] | None:
    redis_client = RedisClient.get(name=config.service_name)

    messages = await redis_client.consume(
        stream=REDIS_SCHEDULED_CRAWL_JOB_STREAM_NAME,
        group=REDIS_DISCOVERY_GROUP_NAME,
        consumer=REDIS_DISCOVERY_CONSUMER_PREFIX + socket.gethostname(),
        count=1,
        block=1000,
        id=">",
    )

    if not messages:
        logger.debug("No crawler job pull request.")
        return None

    msg_id, payload = messages[0]
    logger.debug(f"msg_id {msg_id}, payload {payload}")
    payload = json.loads(payload)

    job = ScheduledCrawlJob.model_validate(payload)
    return msg_id, job
