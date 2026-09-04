import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_example_config_uses_placeholders_only():
    text = (ROOT / "examples" / "main_config.example.yaml").read_text(encoding="utf-8")
    assert "pMax:" in text
    assert "127.0.0.1" in text
    assert "YOUR_SECRET" in text
    assert "ExampleUePool" in text
    assert re.search(r"\b10\.\d+\.\d+\.\d+\b", text) is None
    assert re.search(r"\b192\.168\.\d+\.\d+\b", text) is None
