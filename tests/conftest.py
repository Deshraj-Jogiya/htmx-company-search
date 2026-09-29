import pytest

from app import data


@pytest.fixture(autouse=True)
def reset_companies():
    """Real state, reset between tests: the search results now live in a
    real (in-memory) SQLite table that an inline edit actually mutates,
    so tests need this to stay independent of each other and of test
    execution order."""
    data.reset_db()
    yield
    data.reset_db()
