import yaml
from pathlib import Path

from discovery_engine.config import load_config


def test_load_config_from_yaml(tmp_path: Path):
    config_data = {
        "service_name": "discovery-engine",
        "logging": {"level": "INFO"},
        "sources": [
            {"name": "arxiv", "type": "pdf", "url": "https://export.arxiv.org/api/query"}
        ],
        "topics": ["AI", "ML"],
        "workers": {"count": 2, "queue_size": 500},
        "crawler": {"rate_limit_seconds": 5},
        "redis": {
            "host": "redis",
            "port": 6379,
            "username": "default",
            "password": "password",
        },
        "streams": {
            "scheduled_crawl_job": "pazyr_scheduled_crawl_jobs",
            "processing": "pazyr_processing_jobs",
        },
        "arxiv": {"batch_size": 100},
    }

    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config_data), encoding="utf-8")

    config = load_config(str(config_path))
    assert config.service_name == "discovery-engine"
    assert config.logging.level == "INFO"
    assert config.sources["arxiv"].url == "https://export.arxiv.org/api/query"
    assert config.streams.processing == "pazyr_processing_jobs"
