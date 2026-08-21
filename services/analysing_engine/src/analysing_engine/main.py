import asyncio
import signal
import sys

from analysing_engine.ai.llm import LLMProviderFactory, LLMRequest
from analysing_engine.ai.prompt import PROMPT_TEMPLATE
from analysing_engine.config import config
from analysing_engine.constants import *
from pazyr_core.clients.redis_client import RedisClient
from pazyr_core.clients.postgres_client import PostgresClient
from pazyr_core.logging.logger import get_logger, init_logger, shutdown_logger

from .utils.query_registry import QueryRegistry

shutdown_event = asyncio.Event()
active_tasks: set[asyncio.Task] = set()


async def shutdown():
    pass

async def start():
    logger = get_logger(__name__)

    redis_client = RedisClient.init(
        name=config.service_name,
        redis_url=config.redis.url
    )

    if not await redis_client.ping():
        logger.debug(await redis_client.client.info())
        logger.error("Redis is not rechable")
        shutdown_event.set()
        return

    await redis_client.create_consumer_group(stream=REDIS_PROCESSING_STREAM_NAME, group=REDIS_ANALYSER_GROUP_NAME)

    llm_provider = LLMProviderFactory.create(
        provider=config.ai.llm.provider,
        model=config.ai.llm.model,
        endpoint=config.ai.llm.endpoint,
        api_key=config.ai.llm.api_key.get_secret_value()
    )
    
    postgres_client = PostgresClient.init(
		name=config.service_name,
		dsn=config.database.connection_string
	)
    
    
    
    # response = await llm_provider.generate(
	# 	request=LLMRequest(
	# 		system_prompt=PROMPT_TEMPLATE,
   	# 		prompt="hi"
	# 	)
	# )
    
    # logger.info(f"Response from llm {response.content}")
    
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
    except (asyncio.CancelledError):
        pass
    finally:
        await shutdown()

def run():
    init_logger(level=config.logging.level)
    
    # Disabling logging of litellm.
    import logging
    logging.getLogger("LiteLLM").disabled = True
    logging.getLogger("litellm").disabled = True
    
    logger = get_logger(__name__)
    logger.info("Initializing Analyser Engine.")

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