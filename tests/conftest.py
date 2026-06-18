import pytest


@pytest.fixture
def temp_db_path(tmp_path):
    return str(tmp_path / "test_books.db")
