import asyncio
import signal

from pazyr_core.logger import init_logger, get_logger, shutdown_logger
from pazyr_core.redis_client import init_redis_client, close_redis_client
from pazyr_core import constants

from .crawler.manager import start_crawlers
from .downloader.worker import start_download_workers
from .config import config

shutdown_event = asyncio.Event()
active_tasks: set[asyncio.Task] = set()

def create_tracked_task(coro):
    task = asyncio.create_task(coro)
    active_tasks.add(task)
    task.add_done_callback(active_tasks.discard)
    return task


async def shutdown():
    logger = get_logger(__name__)
    logger.info("Shutdown initiated. Waiting for tasks to complete with timeout of 5 sec...")

    if active_tasks:
        try:
            await asyncio.wait_for(
                asyncio.gather(*active_tasks, return_exceptions=True),
                timeout=5,
            )
        except asyncio.TimeoutError:
            logger.error("Timeout waiting for tasks.")

    logger.info("All tasks completed.")

    await close_redis_client()


async def start():
    logger = get_logger(__name__)

    redis_client = init_redis_client(
        redis_url=config.redis_url,
        group=constants.DEFAULT_GROUP_NAME_REDIS,
        max_len=constants.DEFAULT_STREAM_MAX_LEN_REDIS,
    )
    await redis_client.create_group_for_stream(config.scheduled_crawl_job_stream_name)
    await redis_client.create_group_for_stream(constants.DOWNLOADER_STREAM_NAME_REDIS)
    await redis_client.create_group_for_stream(constants.DEAD_LETTER_QUEUE_STREAM_NAME_REDIS)

    crawler_tasks = start_crawlers(
        shutdown_event=shutdown_event,
        create_task_fn=create_tracked_task,
    )

    downloader_tasks = start_download_workers(
        shutdown_event=shutdown_event,
        create_task_fn=create_tracked_task,
    )

    for task in crawler_tasks + downloader_tasks:
        active_tasks.add(task)
        task.add_done_callback(active_tasks.discard)

    logger.info("Workers started.")

    await shutdown_event.wait()


def _signal_handler():
    logger = get_logger(__name__)
    logger.info("Shutdown signal received")
    shutdown_event.set()

async def main():
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _signal_handler)
    try:
        await start()
        await shutdown_event.wait()
    except (asyncio.CancelledError):
        pass
    finally:
        await shutdown()


# -------------------------------
# Entrypoint
# -------------------------------
def run():
    init_logger(level=config.log_level)
    logger = get_logger(__name__)
    logger.info("Initializing Ingestor")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
    finally:
        logger.info("Shutting down logger...")
        shutdown_logger()


if __name__ == "__main__":
    run()