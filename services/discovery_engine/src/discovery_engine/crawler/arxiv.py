import asyncio
from datetime import UTC, datetime
from xml.etree import ElementTree as ET

import aiohttp
from pazyr_core.clients.redis_client import RedisClient
from pazyr_core.logging.logger import get_logger
from pazyr_core.types import Artifact

from pazyr_core import constants

from ..config import config

log = get_logger(__name__)


class ArxivCrawler:
    def __init__(self):
        # ssl_context = ssl.create_default_context(cafile=certifi.where())
        # connector = aiohttp.TCPConnector(ssl=ssl_context)
        self.session = aiohttp.ClientSession(
            # timeout=aiohttp.ClientTimeout(total=30),
            # connector=connector
        )

    def build_arxiv_query(self, topics):
        category_query = (
            "cat:cs.CL OR cat:cs.LG OR cat:cs.AI OR cat:stat.ML OR cat:cs.CV"
        )
        keyword_query = " OR ".join(f'all:"{topic}"' for topic in topics)
        query = f"({category_query}) AND ({keyword_query})"
        log.debug(f"Built arXiv query: {query}")
        return query

    async def fetch_arxiv_papers(
        self, base_url: str, topics: list, start_idx: int, max_results: int
    ):
        query = self.build_arxiv_query(topics)
        params = {
            "search_query": query,
            "start": start_idx,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }

        log.debug(
            f"Fetching arXiv papers: start_idx={start_idx}, max_results={max_results}"
        )
        try:
            async with self.session.get(base_url, params=params) as response:
                response.raise_for_status()
                log.debug(f"Successfully fetched arXiv papers from offset {start_idx}")
                return await response.text()
        except aiohttp.ClientError as e:
            log.error(f"Failed to fetch arXiv papers: {e}")
            raise

    async def parse_and_filter(self, xml_data, start_date: datetime):
        log.debug(f"Parsing and filtering XML data for papers after {start_date}")

        root = ET.fromstring(xml_data)
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        redis_client = RedisClient.get(name=config.service_name)
        log.info(f"Total entries found are {len(root.findall('atom:entry', ns))}")

        for entry in root.findall("atom:entry", ns):
            try:
                published = entry.find("atom:published", ns).text
                published_dt = (
                    datetime.strptime(published, "%Y-%m-%dT%H:%M:%SZ")
                    .replace(tzinfo=UTC)
                    .date()
                )

                if published_dt < start_date.date():
                    log.debug(f"Filtered out old entry published on {published_dt}")
                    return True  # Since results are sorted by date, we can stop parsing further

                id_url = entry.find("atom:id", ns).text
                arxiv_id = id_url.split("/")[-1]
                pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

                title = str(entry.find("atom:title", ns).text.strip())
                summary = str(entry.find("atom:summary", ns).text.strip())
                tags = [
                    category.attrib["term"]
                    for category in entry.findall("atom:category", ns)
                ]
                authors = [
                    author.find("atom:name", ns).text
                    for author in entry.findall("atom:author", ns)
                ]

                artifact_obj = Artifact(
                    title=title,
                    id=arxiv_id,
                    summary=summary,
                    published=published_dt,
                    url=pdf_url,
                    tags=tags,
                    authors=authors,
                    source="arxiv",
                )

                log.debug(f"Queueing artifact: {arxiv_id} - {title[:50]}")
                await redis_client.push_to_stream(
                    constants.DOWNLOADER_STREAM_NAME_REDIS,
                    artifact_obj.model_dump_json(),
                )
            except Exception as e:
                log.error(f"Error parsing entry {entry}: {e!s}")
                continue

    async def fetch_artifacts(self, topics: list, start_date: datetime):
        log.debug(f"Starting arXiv crawler with topics: {topics}")
        base_url = config.sources["arxiv"].url
        if not base_url:
            log.error("ArXiv base URL not found in config")
            raise ValueError("ArXiv base URL not configured")

        start_idx = 0
        batch_size = config.arxiv_batch_size

        while True:
            log.debug(f"Fetching batch starting at index {start_idx}")
            xml_data = await self.fetch_arxiv_papers(
                base_url=base_url,
                topics=topics,
                start_idx=start_idx,
                max_results=batch_size,
            )

            result = await self.parse_and_filter(xml_data, start_date=start_date)
            if result:
                log.debug("No more relevant papers found, stopping crawler.")
                break

            start_idx += batch_size
            log.debug(
                f"Sleeping for {config.crawler_rate_limit_seconds}s before next batch"
            )
            await asyncio.sleep(config.crawler_rate_limit_seconds)

    async def close(self):
        await self.session.close()


async def crawl_arxiv(
    topics: list, start_date: datetime, semaphore: asyncio.Semaphore
):
    crawler = ArxivCrawler()

    async with semaphore:
        try:
            await crawler.fetch_artifacts(topics, start_date)
        finally:
            await crawler.close()
