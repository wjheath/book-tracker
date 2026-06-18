import csv

import pytest

from book_manager import BookManager
from database import Database


@pytest.fixture
def manager(temp_db_path):
    with Database(temp_db_path) as db:
        yield BookManager(db)


def test_add_and_list_books(manager):
    manager.add_book("Dune", "Frank Herbert", status="read")
    books = manager.list_books()
    assert len(books) == 1
    assert books[0]["title"] == "Dune"
    assert books[0]["status"] == "read"


def test_remove_book(manager):
    manager.add_book("Dune", "Frank Herbert")
    book_id = manager.list_books()[0]["id"]
    manager.remove_book(book_id)
    assert manager.list_books() == []


def test_find_duplicate_is_case_and_whitespace_insensitive(manager):
    manager.add_book("Dune", "Frank Herbert")
    assert manager.find_duplicate("  dune ", " FRANK HERBERT ") is not None
    assert manager.find_duplicate("Foundation", "Isaac Asimov") is None


def test_import_from_csv_skips_duplicates(manager, tmp_path):
    manager.add_book("Dune", "Frank Herbert", status="read")
    csv_path = tmp_path / "import.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Title", "Authors", "Read Status"])
        writer.writerow(["Dune", "Frank Herbert", "read"])  # duplicate, should be skipped
        writer.writerow(["Foundation", "Isaac Asimov", "to-read"])

    count = manager.import_from_csv(str(csv_path))

    assert count == 1
    titles = {b["title"] for b in manager.list_books()}
    assert titles == {"Dune", "Foundation"}


def test_import_from_csv_missing_file_returns_zero(manager):
    assert manager.import_from_csv("does-not-exist.csv") == 0
