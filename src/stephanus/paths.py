"""Project paths; STEPHANUS_HOME can point at another resource library."""

import os
from pathlib import Path

ROOT = Path(os.environ.get("STEPHANUS_HOME", Path(__file__).resolve().parents[2]))
DATA = ROOT / "data"
VENDOR = ROOT / "vendor"
DATABASE = DATA / "stephanus.sqlite"
MANIFEST = ROOT / "resources.json"
