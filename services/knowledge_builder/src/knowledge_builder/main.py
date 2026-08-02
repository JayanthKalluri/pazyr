import asyncio
import os
import shutil
import uuid
import json
import ollama
from typing import List, Dict, Tuple
from pathlib import Path

from .config import config
from pazyr_core import constants
from pazyr_core.types import JobObject
from pazyr_core.clients.redis_client import init_redis_client, close_redis_client
from pazyr_core.clients.weaviate_client import init_weaviate_client, close_weaviate_client
from pazyr_core.clients.postgres_client import PostgresClient
from pazyr_core.logging.logger import init_logger, get_logger, shutdown_logger

def generate_flow_id() -> uuid.UUID:
    id = uuid.uuid4()
    return id


def move_to_completed(source_path: Path) -> bool:
    try:
        os.makedirs(config.completed_folder_path, exist_ok=True)

        folder_path, file_name = os.path.split(source_path)
        destiination_path = os.path.join(config.completed_folder_path, file_name)

        shutil.move(source_path, destiination_path)
        return True
    except Exception as e:
        return False


async def embed_text(text: str):
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None, lambda: ollama.embeddings(model="nomic-embed-text", prompt=text)
    )
    return response["embedding"]


# STAGE-1
def extract_data(job_payload: JobObject) -> Dict:
    data = {}

    # extracting the abstract
    # pdf_id = job_payload.artifact.id
    # response = requests.get(f"https://arxiv.org/abs/{pdf_id}")
    # soup = BeautifulSoup(response.text, "html.parser")

    # abstract_block = soup.find("blockquote", class_="abstract")
    # descriptor = abstract_block.find("span", class_="descriptor")
    # if descriptor:
    #     descriptor.decompose()

    # abstract = abstract_block.get_text(strip=True)

    data["title"] = job_payload.artifact.title
    data["abstract"] = job_payload.artifact.summary
    data["metadata"] = {
        "source": job_payload.artifact.source,
        "type": "pdf",
        "website": job_payload.artifact.pdf_url,
    }

    return data


# STAGE-2
def process_data(data: Dict) -> Tuple[str, Dict]:
    processed_data = ""
    for k, v in data.items():
        if k != "metadata":
            processed_data += f"{str(k).capitalize()}: {v}\n"
    processed_data = processed_data.rstrip("\n")

    metadata = data.get("metadata")
    return (processed_data, metadata)


# STAGE-3
async def chunk_data(data: str) -> List[float]:
    chunks = await embed_text(data)
    return chunks


# STAGE-4
async def ingest_data(
    chunks: List[float], metadata: Dict, weaviate_client: WeaviateClient, job_id: str
) -> bool:
    try:
        await weaviate_client.insert_object(
            uuid=job_id,
            vector=chunks,
            properties={
                "title": metadata.get("title"),
                "summary": metadata.get("abstract"),
            },
        )
        return True
    except Exception as e:
        print(f"Exception {e}, ingest_data")
        return False


# PIPELINE
async def ingestion_main_flow(
    job_payload: dict,
    job_id: str,
    weaviate_client: WeaviateClient,
    postgres_client: PostgresClient,
):
    """
    End to end flow of ingestion piepline.
    """
    try:
        # 1. Extracting phase
        extracted_data_dict = extract_data(job_payload)

        # 2. Processing phase
        processed_data_str, metadata = process_data(extracted_data_dict)

        # 3. Chunking phase
        chunks = await chunk_data(processed_data_str)

        # 4. Ingestion phase
        await ingest_data(chunks, metadata, weaviate_client, job_id)

        status = move_to_completed(source_path=job_payload.artifact.location)
        return status
    except Exception as e:
        print(f"Exception {e}, ingestion_main_flow")
        return False


def get_postgres_connection_string():
    password = os.getenv("POSTGRES_PASSWORD", "")
    if not password:
        raise ValueError("POSTGRES_PASSWORD environment variable is set to None.")

    user_name = config.postgres.user
    pg_host = config.postgres.host
    pg_port = config.postgres.port
    db_name = config.postgres.database
    conn_string = f"postgresql://{user_name}:{password}@{pg_host}:{pg_port}/{db_name}"

    return conn_string


async def create_job_table(pg_client: PostgresClient, **vargs):
    try:
        table_name = vargs.get("table_name", "")
        query_template = config.queries.create_job_table.query
        query = query_template.format(table_name=table_name)
        await pg_client.run_query(query)
        return True
    except Exception as e:
        raise


async def main():
    logger = get_logger(__name__)

    redis_client = init_redis_client(
        redis_url=config.redis_url,
        group=constants.DEFAULT_GROUP_NAME_REDIS,
        max_len=constants.DEFAULT_STREAM_MAX_LEN_REDIS,
    )
    await redis_client.create_group_for_stream(config.processing_stream_name)
    logger.debug("Redis client initialised.")

    weaviate_client = init_weaviate_client(
        host=config.weaviate.host,
        http_port=config.weaviate.http_port,
        grpc_port=config.weaviate.grpc_port,
        collection_name=config.weaviate_collection_name
    )
    await weaviate_client.instantiate_and_connect()
    # TODO: Pass collection from here only can hardcode the collections properties there.
    await weaviate_client.ensure_collection()
    logger.debug("Weaviate client initialised.")

    pg_conn_string = get_postgres_connection_string()
    pg_client = PostgresClient(dsn=pg_conn_string)
    await pg_client.connect()
    await create_job_table(pg_client, table_name=config.jobs_table_name)

    # Process messages concurrently for true async
    tasks = []
    semaphore = asyncio.Semaphore(5)  # Limit concurrent processing

    while True:
        # Pull multiple messages at once
        messages = redis_client.pull(count=1)
        if not messages:
            await asyncio.sleep(0.1)  # Small delay to prevent tight loop
            continue

        # Process each message concurrently
        for msg_id, job_payload in messages:
            if not isinstance(job_payload, dict):
                job_payload = json.loads(job_payload)

            job_obj = JobObject.model_validate(job_payload)

            async def process_single(msg_id, job_obj):
                async with semaphore:
                    try:
                        pipeline_id = generate_flow_id()
                        status = await ingestion_main_flow(
                            job_obj,
                            job_id=pipeline_id,
                            weaviate_client=weaviate_client,
                            postgres_client=pg_client,
                        )
                        if status:
                            redis_client.ack(msg_id)
                        else:
                            print(f"Failed to process message {msg_id}")
                    except Exception as e:
                        print(f"Error processing message {msg_id}: {e}")

            task = asyncio.create_task(process_single(msg_id, job_obj))
            tasks.append(task)
            
            break

        # Clean up completed tasks and prevent unbounded growth
        # tasks = [t for t in tasks if not t.done()]
        # if len(tasks) > 20:
        #     # Wait for oldest tasks to complete
        #     await asyncio.gather(*tasks[:10])
        #     tasks = tasks[10:]
        await asyncio.gather(*tasks)

def run():
    init_logger(level=config.log_level)
    logger = get_logger(__name__)
    logger.info("Initializing Knowledge builder.")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
    finally:
        logger.info("Shutting down logger....")
        shutdown_logger()


if __name__ == "__main__":
    run()
