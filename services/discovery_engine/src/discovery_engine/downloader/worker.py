import asyncio
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

import aiofiles
import aiohttp
from ingestor.config import config
from pazyr_core.clients.redis_client import get_redis_client
from pazyr_core.logging.logger import get_logger
from pazyr_core.types import Artifact, JobObject

from pazyr_core import constants

logger = get_logger(__name__)


def start_download_workers(shutdown_event, create_task_fn):
    return [
        create_task_fn(download_worker(i, shutdown_event))
        for i in range(config.worker_count)
    ]


class DownloadWorker:
    def __init__(self, worker_id: int):
        self.worker_id = worker_id
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=config.download_timeout_seconds)
        )

    async def download_artifact(self, artifact: Artifact) -> bytes | None:
        url = artifact.url
        logger.debug(f"[{self.worker_id}] Starting download for URL: {url}")
        for attempt in range(config.download_retry_count):
            try:
                logger.debug(
                    f"[{self.worker_id}] Download attempt {attempt + 1}/{config.download_retry_count} for URL: {url}"
                )
                async with self.session.get(url) as response:
                    response.raise_for_status()
                    content = await response.read()
                    logger.debug(
                        f"[{self.worker_id}] Successfully downloaded {len(content)} bytes from {url}"
                    )
                    return content
            except aiohttp.ClientError as e:
                wait_time = 2**attempt
                logger.warning(
                    f"[{self.worker_id}] Download attempt {attempt + 1} failed for {url}: {e}. Retrying in {wait_time}s..."
                )
                await asyncio.sleep(wait_time)

        logger.error(
            f"[{self.worker_id}] Failed to download {url} after {config.download_retry_count} attempts"
        )
        return None

    async def close(self):
        await self.session.close()


async def handle_failed_download(artifact: Artifact):
    logger = get_logger(__name__)
    redis_client = get_redis_client(name="ingestor")
    logger.info(f"Pushing {artifact.title} into DQL.")
    await redis_client.push_to_stream(
        stream_name=constants.DEAD_LETTER_QUEUE_STREAM_NAME_REDIS, payload=artifact
    )


def create_job_object(artifact: Artifact, worker_id: int) -> JobObject:
    job_id = str(uuid.uuid4())
    logger.debug(f"[{worker_id}] Creating JobObject with job_id={job_id}")

    return JobObject(artifact=artifact, id=job_id, created_at=datetime.now(UTC))


async def pull_download_job() -> tuple[str, Artifact] | None:
    redis_client = get_redis_client(name="ingestor")
    messages = await redis_client.read_from_stream(
        stream_name=constants.DOWNLOADER_STREAM_NAME_REDIS,
        consumer=constants.DOWNLOADER_CONSUMER_NAME_REDIS,
        count=1,
        block=1000,
    )

    if not messages:
        return None

    msg_id, payload_str = messages[0]
    payload = json.loads(payload_str)
    artifact_obj = Artifact.model_validate(payload)
    return msg_id, artifact_obj


async def download_worker(worker_id: int, shutdown_event):
    logger.info(f"[{worker_id}] Starting Downloader Worker. ")

    download_worker_instance = DownloadWorker(worker_id)
    redis_client = get_redis_client(name="ingestor")

    try:
        while not shutdown_event.is_set():
            try:
                download_job = await pull_download_job()
                if not download_job:
                    logger.debug(
                        f"[{worker_id}] No download jobs available, sleeping briefly"
                    )
                    await asyncio.sleep(0.1)
                    continue
                msg_id, artifact_obj = download_job

                downloaded_content = await download_worker_instance.download_artifact(
                    artifact_obj
                )
                if not downloaded_content:
                    raise Exception(
                        f"Failed to download artifact from URL: {artifact_obj.url}"
                    )

                # write the downloaded_content into filesystem
                file_location = Path(config.storage_path) / f"{artifact_obj.id}.pdf"
                file_location.parent.mkdir(parents=True, exist_ok=True)
                async with aiofiles.open(file_location, "wb") as f:
                    await f.write(downloaded_content)

                # Add location to artifact_obj
                artifact_obj.location = str(file_location)

                job_obj = create_job_object(artifact=artifact_obj, worker_id=worker_id)

                # Push the job to downstream
                await redis_client.push_to_stream(
                    config.processing_stream_name, job_obj.model_dump_json()
                )

                # Ack the download_job
                await redis_client.ack(constants.DOWNLOADER_STREAM_NAME_REDIS, msg_id)

                logger.info(
                    f"[{worker_id}] Successfully processed download job {job_obj.id} for artifact {artifact_obj.id}"
                )

            except Exception as e:
                logger.warning(f"[{worker_id}] Error in download worker loop: {e}")
                await handle_failed_download(artifact=artifact_obj)
    finally:
        await download_worker_instance.close()
        logger.info(f"[{worker_id}] Worker shutdown complete.")
