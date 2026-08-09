import asyncio
import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from discovery_engine.crawler.arxiv import ArxivCrawler


@pytest.fixture(autouse=True)
def patch_aiohttp_session(monkeypatch):
    mock_session = Mock()
    mock_session.get = AsyncMock()
    mock_session.close = AsyncMock()
    monkeypatch.setattr("discovery_engine.crawler.arxiv.aiohttp.ClientSession", Mock(return_value=mock_session))


def make_xml_entry(arxiv_id: str, published: str, title: str, summary: str):
    return f"""<entry>
        <id>http://arxiv.org/abs/{arxiv_id}</id>
        <published>{published}</published>
        <title>{title}</title>
        <summary>{summary}</summary>
        <category term=\"cs.AI\" />
        <author>
            <name>Author One</name>
        </author>
    </entry>"""


def make_feed(entries: str):
    return f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
    <feed xmlns=\"http://www.w3.org/2005/Atom\">{entries}</feed>"""


def test_build_arxiv_query_contains_topics():
    crawler = ArxivCrawler()
    try:
        query = crawler.build_arxiv_query(["AI", "NLP"])
        assert "all:\"AI\"" in query
        assert "all:\"NLP\"" in query
        assert "cat:cs.CL" in query
    finally:
        asyncio.run(crawler.close())


def test_parse_and_filter_publishes_artifact():
    mock_publish = AsyncMock()
    mock_cfg = Mock()
    mock_cfg.service_name = "discovery-engine"
    mock_cfg.streams = Mock(processing="pazyr_processing_jobs")

    with patch("discovery_engine.crawler.arxiv.config", mock_cfg):
        with patch("pazyr_core.clients.redis_client.RedisClient.get", return_value=Mock(publish=mock_publish)):
            crawler = ArxivCrawler()
            try:
                xml_data = make_feed(make_xml_entry("1234.5678v1", "2026-06-01T12:00:00Z", "Hello World", "A summary."))
                result = asyncio.run(crawler.parse_and_filter(xml_data, datetime(2026, 1, 1, tzinfo=UTC)))
                assert result is None
                mock_publish.assert_awaited_once()
                published_payload = mock_publish.await_args.args[1]
                payload_obj = json.loads(published_payload)
                assert payload_obj["id"] == "1234.5678v1"
                assert payload_obj["title"] == "Hello World"
            finally:
                asyncio.run(crawler.close())


def test_parse_and_filter_stops_on_old_entry():
    mock_publish = AsyncMock()
    mock_cfg = Mock()
    mock_cfg.service_name = "discovery-engine"
    mock_cfg.streams = Mock(processing="pazyr_processing_jobs")

    with patch("discovery_engine.crawler.arxiv.config", mock_cfg):
        with patch("pazyr_core.clients.redis_client.RedisClient.get", return_value=Mock(publish=mock_publish)):
            crawler = ArxivCrawler()
            try:
                xml_data = make_feed(make_xml_entry("1234.5678v1", "2020-01-01T12:00:00Z", "Old Paper", "An old summary."))
                result = asyncio.run(crawler.parse_and_filter(xml_data, datetime(2026, 1, 1, tzinfo=UTC)))
                assert result is True
                mock_publish.assert_not_awaited()
            finally:
                asyncio.run(crawler.close())
