import asyncio
import signal
import sys

from pazyr_core.clients.redis_client import RedisClient
from pazyr_core.logging.logger import get_logger, init_logger, shutdown_logger

from .config import config
from .constants import *
from .crawler.manager import start_crawlers

shutdown_event = asyncio.Event()
active_tasks: set[asyncio.Task] = set()


def create_tracked_task(coro):
    task = asyncio.create_task(coro)
    active_tasks.add(task)
    task.add_done_callback(active_tasks.discard)
    return task


async def shutdown():
    logger = get_logger(__name__)
    logger.info(
        "Shutdown initiated. Waiting for tasks to complete with timeout of 5 sec..."
    )

    if active_tasks:
        try:
            await asyncio.wait_for(
                asyncio.gather(*active_tasks, return_exceptions=True),
                timeout=5,
            )
        except TimeoutError:
            logger.error("Timeout waiting for tasks.")

    logger.info("All tasks completed.")

    await RedisClient.shutdown(name=config.service_name)


async def start():
    logger = get_logger(__name__)

    redis_client = RedisClient.init(
        name=config.service_name, redis_url=config.redis.url
    )
    if not await redis_client.ping():
        logger.error("Redis is not rechable")
        await shutdown()

    await redis_client.create_consumer_group(
        stream=REDIS_SCHEDULED_CRAWL_JOB_STREAM_NAME, group=REDIS_DISCOVERY_GROUP_NAME
    )

    crawler_tasks = start_crawlers(
        shutdown_event=shutdown_event,
        create_task_fn=create_tracked_task,
    )

    for task in crawler_tasks:
        active_tasks.add(task)
        task.add_done_callback(active_tasks.discard)

    logger.info("Workers started.")

    await shutdown_event.wait()


def _signal_handler():
    logger = get_logger(__name__)
    logger.info("Shutdown signal received.")
    shutdown_event.set()


async def main():
    loop = asyncio.get_running_loop()
    if sys.platform != "win32":  # Only register signals on Unix
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, _signal_handler)
    else:
        # On Windows, rely on KeyboardInterrupt
        pass
    try:
        await start()
        await shutdown_event.wait()
    except asyncio.CancelledError:
        pass
    finally:
        await shutdown()


# -------------------------------
# Entrypoint
# -------------------------------
def run():
    init_logger(level=config.logging.level)
    logger = get_logger(__name__)
    logger.info("Initializing Discovery Engine.")

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
