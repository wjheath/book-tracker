import sqlite3

import pytest

from database import Database


def test_context_manager_opens_and_closes_connection(temp_db_path):
    with Database(temp_db_path) as db:
        assert db.connection is not None
        db.execute_query("INSERT INTO books (title, author) VALUES (?, ?)", ("Dune", "Frank Herbert"))
        assert len(db.fetch_all("SELECT * FROM books")) == 1

    with pytest.raises(sqlite3.ProgrammingError):
        db.connection.execute("SELECT 1")


def test_create_table_creates_all_expected_tables(temp_db_path):
    with Database(temp_db_path) as db:
        rows = db.fetch_all("SELECT name FROM sqlite_master WHERE type='table'")
    table_names = {r["name"] for r in rows}
    assert {"books", "rejected_suggestions", "conversations", "reader_profile_cache", "user_settings"} <= table_names


def test_reconnecting_to_existing_db_does_not_raise(temp_db_path):
    with Database(temp_db_path) as db:
        db.execute_query("INSERT INTO books (title, author) VALUES (?, ?)", ("Dune", "Frank Herbert"))

    # Re-running create_table (including the ALTER TABLE migrations) against
    # an already-migrated database must be a no-op, not an error.
    with Database(temp_db_path) as db:
        rows = db.fetch_all("SELECT * FROM books")
    assert len(rows) == 1


def test_fetch_all_returns_list_of_dicts(temp_db_path):
    with Database(temp_db_path) as db:
        db.execute_query(
            "INSERT INTO books (title, author, status) VALUES (?, ?, ?)",
            ("Dune", "Frank Herbert", "read"),
        )
        rows = db.fetch_all("SELECT title, author, status FROM books")
    assert rows == [{"title": "Dune", "author": "Frank Herbert", "status": "read"}]
