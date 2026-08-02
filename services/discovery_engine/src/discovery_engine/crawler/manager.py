import asyncio
import json

from pazyr_core.clients.redis_client import RedisClient
from pazyr_core.logging.logger import get_logger
from pazyr_core.types import ScheduledCrawlJob

from pazyr_core import constants

from ..config import config
from .arxiv import crawl_arxiv

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
        create_task_fn(process_job(msg_id, job, shutdown_event))


async def process_job(msg_id: str, job: ScheduledCrawlJob, shutdown_event):
    redis_client = RedisClient.get(name=config.service_name)

    if shutdown_event.is_set():
        return

    try:
        await handle_crawler_job(job, shutdown_event)
        await redis_client.ack(config.scheduled_crawl_job_stream_name, msg_id)
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
    messages = await redis_client.read_from_stream(
        stream_name=config.scheduled_crawl_job_stream_name,
        consumer=constants.CRAWLER_CONSUMER_NAME_REDIS,
        count=1,
        block=1000,
    )

    if not messages:
        return None

    msg_id, payload = messages[0]
    payload = json.loads(payload)

    job = ScheduledCrawlJob.model_validate(payload)
    return msg_id, job
