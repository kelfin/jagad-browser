import os
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))


@pytest.fixture(scope="session")
def repo() -> Path:
    return REPO


def network_allowed() -> bool:
    return os.environ.get("JAGAD_OFFLINE") != "1"
