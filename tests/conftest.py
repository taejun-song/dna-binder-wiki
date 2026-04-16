import pytest
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"

@pytest.fixture
def sample_csv():
    return FIXTURES_DIR / "sample_candidates.csv"
