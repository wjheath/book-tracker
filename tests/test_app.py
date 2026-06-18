import pytest

import app as app_module


@pytest.fixture
def client(temp_db_path, monkeypatch):
    monkeypatch.setattr(app_module, "DB_PATH", temp_db_path)
    app_module.app.config["TESTING"] = True
    return app_module.app.test_client()


def test_health_check(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True


def test_add_list_and_delete_book(client):
    resp = client.post("/api/books", json={"title": "Dune", "author": "Frank Herbert", "status": "read"})
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True

    data = client.get("/api/books").get_json()
    assert data["count"] == 1
    book = data["books"][0]
    assert book["title"] == "Dune"

    resp = client.delete(f"/api/books/{book['id']}")
    assert resp.get_json()["success"] is True
    assert client.get("/api/books").get_json()["count"] == 0


def test_add_book_requires_title_and_author(client):
    resp = client.post("/api/books", json={"title": "", "author": ""})
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False


def test_add_duplicate_book_is_rejected(client):
    client.post("/api/books", json={"title": "Dune", "author": "Frank Herbert"})
    resp = client.post("/api/books", json={"title": "dune", "author": "frank herbert"})
    assert resp.status_code == 409
    assert resp.get_json()["success"] is False


def test_update_book_status_sets_read_date(client):
    client.post("/api/books", json={"title": "Dune", "author": "Frank Herbert"})
    book_id = client.get("/api/books").get_json()["books"][0]["id"]

    resp = client.put(f"/api/books/{book_id}/status", json={"status": "read"})
    assert resp.get_json()["success"] is True

    book = client.get("/api/books").get_json()["books"][0]
    assert book["status"] == "read"
    assert book["read_date"]


def test_update_book_status_rejects_invalid_status(client):
    client.post("/api/books", json={"title": "Dune", "author": "Frank Herbert"})
    book_id = client.get("/api/books").get_json()["books"][0]["id"]

    resp = client.put(f"/api/books/{book_id}/status", json={"status": "not-a-real-status"})
    assert resp.status_code == 400
