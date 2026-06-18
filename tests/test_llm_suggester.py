import llm_suggester as llm_suggester_module


def test_dry_run_when_no_api_key(monkeypatch):
    monkeypatch.setattr(llm_suggester_module, "OPENAI_API_KEY", None)
    suggester = llm_suggester_module.LLM_Suggester()
    assert suggester.client is None


def test_suggest_books_returns_empty_list_in_dry_run(monkeypatch):
    monkeypatch.setattr(llm_suggester_module, "OPENAI_API_KEY", None)
    suggester = llm_suggester_module.LLM_Suggester()
    history = [{"title": "Dune", "author": "Frank Herbert", "status": "read"}]
    assert suggester.suggest_books(history, all_books=history, num_suggestions=3) == []


def test_suggest_books_returns_empty_list_for_no_reading_history(monkeypatch):
    monkeypatch.setattr(llm_suggester_module, "OPENAI_API_KEY", None)
    suggester = llm_suggester_module.LLM_Suggester()
    assert suggester.suggest_books([], all_books=[]) == []
