import os
import yaml
from pazyr_core.settings import KBConfig as Config

def load_config(config_path: str) -> Config:
    with open(config_path, "r", encoding="utf-8") as f:
        yaml_content = yaml.safe_load(f)

    config = Config.model_validate(yaml_content)
    config.consumer = f"worker_{os.getenv('WORKER_ID', '')}"
    return config


config_path = os.getenv("CONFIG_FILEPATH", "./config/knowledge_builder/config.yaml")

if not config_path:
    raise RuntimeError(f"Config file path is empty, Set the CONFIG_FILEPATH env variable.")
config = load_config(config_path)