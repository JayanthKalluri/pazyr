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

