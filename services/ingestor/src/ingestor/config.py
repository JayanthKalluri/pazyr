import os
import yaml
from pazyr_core.models import IngestorConfig as Config

# Load configuration from YAML file
def load_config(config_path: str) -> Config:
    with open(config_path, "r", encoding="utf-8") as f:
        yaml_content = yaml.safe_load(f)

    if "sources" in yaml_content:
        source_list = yaml_content.get("sources", [])
        yaml_content["sources"] = {item["name"]: item for item in source_list}
        
    config = Config.model_validate(yaml_content)
    return config


# Load config at module level
config_path = os.getenv("CONFIG_FILEPATH", "./config/ingestor/config.yaml")
if not config_path:
    raise Exception(f"Config file path is empty, Set the CONFIG_FILEPATH env variable.")

config = load_config(config_path)