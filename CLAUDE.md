# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Flask + SQLite book tracking app with AI-powered recommendations. Single-user, single SQLite file (`data/books.db`), vanilla-JS single-page frontend served directly by Flask (no build step, no frontend framework).

## Commands

```bash
pip install -r requirements.txt       # install runtime deps (Flask, langgraph, langchain-openai, etc.)
pip install -r requirements-dev.txt   # runtime deps + pytest
python src/app.py                     # run the Flask server directly → http://127.0.0.1:5000
python run_ui.py                      # launcher: starts Flask in a subprocess + opens browser
python src/main.py                    # interactive CLI menu (add/list/suggest, no web UI)
start.bat                             # Windows double-click launcher

pytest                                # run the full test suite (tests/, see pytest.ini)
pytest tests/test_book_manager.py     # run a single test file
pytest tests/test_app.py::test_health_check  # run a single test
```

Tests live in `tests/` and import `src/` modules directly (`from database import Database`) via the `pythonpath = src` setting in `pytest.ini` — no `src.` package prefix. They run against a temporary SQLite file per test (`temp_db_path` fixture in `tests/conftest.py`), never the real `data/books.db`, and never call the OpenAI API (LLM tests force dry-run by monkeypatching `OPENAI_API_KEY` to `None`). There's no linter configured.

Requires a `.env` file (see `.env.example`) for `OPENAI_API_KEY`; the app runs in degraded "dry-run" mode without one (see below).

## Architecture

**Flask serves both the API and the SPA from `src/`**: `app.py` sets `static_folder=os.path.dirname(__file__)` so `src/index.html`, `src/app.js`, `src/styles.css` are served directly — there's no `templates/`/`static/` split. `/` returns `index.html`; everything else is JSON under `/api/*` (~26 routes in `src/app.py`).

**Layering**:
- `database.py` — thin SQLite wrapper. `Database` is a context manager (`__enter__`/`__exit__`); `create_table()` runs on every `connect()` and includes `ALTER TABLE ... ADD COLUMN` migrations wrapped in `try/except` (so adding a column = add a line here, no separate migration system).
- `book_manager.py` — `BookManager` wraps a `Database` instance for CRUD + StoryGraph CSV import (`import_from_csv`, case-insensitive column matching, dedupes via `find_duplicate`).
- `llm_suggester.py` — `LLM_Suggester`: one-shot "give me N suggestions" using the OpenAI client directly (not LangGraph). Switches between raw reading history and a `ReaderProfile`-distilled summary once the library exceeds `_LARGE_LIBRARY_THRESHOLD` (50 read books) to avoid diluting the prompt.
- `chat_engine.py` — `BookChatEngine`: multi-turn conversational recommendations via LangGraph (`StateGraph` in `_build_graph()`). Nodes: `classify_intent` → `check_guardrails` → routes to `gather_context` / `generate_recommendations` / `answer_library_query` / `casual_chat` / `handle_off_topic` / `handle_library_update` / `handle_blocked`. Conversation state (`messages`, `gathered_preferences`) is persisted as JSON in the `conversations` table and reloaded per request — there's no in-memory session, only a singleton engine instance (`_chat_engine` in `app.py`) reused across requests.
- `reader_profile.py` — `ReaderProfile.build()` computes 7 analysis dimensions (genres, authors, pace, recency, series preference, library stats, summary) from the book list; results are cached in `reader_profile_cache`. Genre enrichment optionally calls the Open Library API (`_fetch_ol_genre`).
- `config.py` — all environment loading. `OPENAI_API_KEY` absent → app still runs, AI features degrade gracefully rather than failing.
- `prompt_loader.py` — every LLM prompt (suggestion, intent classifier, guardrails, casual/off-topic/library-query/library-update handlers) is a file in `prompts/*.txt`, loaded by `load_prompt(filename, hardcoded_default)`. Edit the `.txt` file to change model behavior; no env override needed unless you want to bypass the file entirely (`CUSTOM_PROMPT_TEMPLATE` env var does that for the suggestion prompt only).

**Database**: one file, four tables — `books`, `rejected_suggestions` (thumbs-down feedback), `conversations` (chat persistence), `reader_profile_cache`, plus a `user_settings` key/value table (e.g. favorite authors). Schema lives only in `database.py::create_table()` — there are no `.sql` migration files.

## Conventions that matter here

- **Always `with Database(DB_PATH) as db:`** — every route opens/closes its own connection this way. Never hold a `Database` instance across requests or call `.close()` manually (including in `main.py`'s CLI loop — it wraps the whole menu loop in one `with` block).
- **None-safety on book fields**: use `book.get('field') or 'default'`, not `book.get('field', 'default')` — SQLite can return explicit `NULL`/`None` for a present key, which the two-arg form won't catch.
- **LLM response content can be `None`**: guard with `response.content if response.content is not None else ''` before `.strip()`/`.format()`.
- **Model fallback**: `OPENAI_MODEL` (default `gpt-4o-mini`) is tried first; `GPT_PREFERRED_MODELS` (comma list in `.env`) is the fallback chain. Don't hardcode model names in new code — read from `config.py`.
- **Frontend XSS**: `src/index.html`/`app.js` use `data-*` attributes + an `escapeHtml()` helper instead of inlining user content into `onclick="..."` strings. Follow this pattern for any new dynamic HTML.
- **Frontend rendering**: `renderFilteredBooks()` is the only function that should mutate `filteredBooks`/`currentPage`; `renderBooks()` takes no arguments and reads `filteredBooks` directly. Don't call `renderBooks(someArray)`.
- Imports inside `src/` are flat/absolute (`from database import Database`, not `from src.database import ...`) — both `app.py` and `main.py` rely on `src/` being on `sys.path` (via cwd or `run_ui.py`'s `sys.path.insert`).
