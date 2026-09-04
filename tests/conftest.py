from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def example_yaml() -> Path:
    return ROOT / "examples" / "main_config.example.yaml"
