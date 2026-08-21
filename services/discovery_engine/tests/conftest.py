import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "pazyr_core" / "src"))
sys.path.insert(0, str(ROOT / "services" / "discovery_engine" / "src"))

os.environ.setdefault(
    "CONFIG_FILEPATH",
    str(ROOT / "config" / "discovery_engine.yaml"),
)
