# Copilot Instructions for Book Tracker & Suggester

## Project Overview

**Book Tracker & Suggester** is a Python Flask web app that manages a reading library and generates AI-powered book recommendations. It has 239 pre-loaded books, a SQLite database, and integrates with OpenAI's API for recommendations.

## Architecture

### Core Components

1. **Backend (Flask)**
   - [src/app.py](../src/app.py) - Flask API with REST endpoints (`/api/books`, `/api/suggestions`)
   - Routes handle: list books, add/delete books, update status, generate LLM suggestions
   - CORS enabled for frontend communication

2. **Data Layer**
   - [src/database.py](../src/database.py) - SQLite wrapper with schema: `id`, `title`, `author`, `status`, `read_date`
   - Connection pattern: `db.connect()`, `db.fetch_all()`, `db.execute_query()`, `db.close()`
   - Always close DB connections after use (see `get_books()` in app.py for pattern)

3. **Business Logic**
   - [src/book_manager.py](../src/book_manager.py) - BookManager class for CRUD operations and CSV imports
   - LLM layer: [src/llm_suggester.py](../src/llm_suggester.py) - LLM_Suggester with model fallback and dry-run support

4. **Frontend (Single Page)**
   - [src/index.html](../src/index.html) - Vanilla JS (no frameworks), ~772 lines
   - Tabs: Dashboard, Library, Suggestions
   - CSS custom properties (--primary, --secondary, etc.) for theming
   - API calls via `fetch()` to `/api/*` endpoints

### Configuration & Environment

- [src/config.py](../src/config.py) - Centralized config loaded from `.env` or defaults
  - Key vars: `OPENAI_API_KEY`, `OPENAI_MODEL`, `GPT_PREFERRED_MODELS` (fallback list)
  - Custom prompts: loads from `prompts/book_suggestion.txt` if exists, else uses `DEFAULT_PROMPT_TEMPLATE`
  - App runs in "dry-run" mode if no API key (graceful degradation)

## Critical Patterns

### Graceful Degradation / Dry-Run Mode
- If `OPENAI_API_KEY` is missing, LLM features are disabled but the app still runs
- See [src/llm_suggester.py:21-29](../src/llm_suggester.py#L21-L29) - `if not self.api_key: self.client = None`
- **When modifying**: Preserve this pattern for robustness; don't assume API key exists

### Model Fallback Strategy
- `OPENAI_MODEL` is primary choice (default: `gpt-5.1`)
- If model unavailable, tries models in `GPT_PREFERRED_MODELS` list
- Current list: `gpt-5.1,gpt-5-mini,gpt-3.5-turbo`
- **When adding features**: Respect this fallback chain; don't hard-code model names

### Book Status Values
- Valid statuses: `'read'`, `'to-read'`, `'currently-reading'`
- Used in filtering, CSV imports, and API responses
- **When modifying**: Update stats calculation in [src/app.py](../src/app.py#L48-L52) if adding new statuses

### CSV Import Pattern
- Imports from StoryGraph export format (CSV with `Title`, `Authors`, `Read Status` columns)
- Maps `Read Status` → `status` field (lowercased)
- Called via [src/import_books.py](../src/import_books.py) or CLI in [src/main.py](../src/main.py)
- Path configurable via `.env` (`CSV_IMPORT_PATH`)

## Data Flows

### Add/Update Book Flow
1. Frontend POST `/api/books` with `{title, author, status, read_date}`
2. [src/app.py](../src/app.py#L74-L95) validates & calls `BookManager.add_book()`
3. BookManager executes `INSERT` via Database
4. Return JSON: `{success: bool, book: {...}, error?: string}`

### Get Suggestions Flow
1. Frontend POST `/api/suggestions` with `{count: 3|5|10}`
2. [src/app.py](../src/app.py#L170-L200) retrieves read books, builds prompt
3. LLM_Suggester formats books list, calls OpenAI API
4. Parse response, return list of `{title, author, reason}`
5. If API fails or key missing, return empty list (no error thrown)

### Database Schema
```sql
CREATE TABLE books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    read_date TEXT,           -- ISO format (YYYY-MM-DD) or NULL
    status TEXT DEFAULT 'to-read'
);
```

## Development Workflows

### Running the App
- **Web UI**: `python src/app.py` → visit `http://127.0.0.1:5000`
- **CLI**: `python src/main.py` (interactive menu)
- **Windows launcher**: Double-click `start_ui_simple.bat`

### Testing
- Test files: [src/test_suggester.py](../src/test_suggester.py), [test_enhanced_suggestions.py](../test_enhanced_suggestions.py)
- Import and test: `from src.llm_suggester import LLM_Suggester`

### Debugging Database
- Use [src/inspect_db.py](../src/inspect_db.py) to query/inspect the SQLite database
- Or run [inspect_db.py](../inspect_db.py) from root

## Code Conventions

1. **Imports**: Use absolute imports within `src/` (e.g., `from database import Database`)
2. **Error Handling**: Return JSON `{success: false, error: "message"}` in Flask routes; log warnings for missing config
3. **Database Cleanup**: Always call `db.close()` after use (pattern in [src/app.py](src/app.py#L59))
4. **Path Resolution**: Use `os.path.dirname(__file__)` for relative paths; use `os.path.join()` for portability
5. **Constants**: Centralize in `config.py`; use environment variables for deployment

## Key Files Quick Reference

| File | Purpose | Key Functions |
|------|---------|---|
| [src/app.py](../src/app.py) | Flask API | `get_books()`, `add_book()`, `suggest_books()`, `/api/*` routes |
| [src/database.py](../src/database.py) | SQLite ops | `connect()`, `fetch_all()`, `execute_query()`, `close()` |
| [src/book_manager.py](../src/book_manager.py) | Business logic | `add_book()`, `remove_book()`, `list_books()`, `import_from_csv()` |
| [src/llm_suggester.py](src/llm_suggester.py) | AI suggestions | `get_suggestions()`, model fallback, prompt rendering |
| [src/config.py](src/config.py) | Configuration | Environment loading, defaults, prompt file resolution |
| [src/index.html](src/index.html) | Frontend UI | Tabs, forms, API calls, styling |

## Common Tasks

### Add a New Book Status
1. Update status validation in [src/app.py](../src/app.py#L75-L80)
2. Update stats calculation in [src/app.py](../src/app.py#L48-L52)
3. Update frontend filter buttons in [src/index.html](../src/index.html#L400+)

### Customize AI Prompt
- Edit [prompts/book_suggestion.txt](../prompts/book_suggestion.txt) or set `CUSTOM_PROMPT_TEMPLATE` in `.env`
- Format uses `{books_list}` and `{num_suggestions}` placeholders

### Handle API Errors
- Try/catch blocks return `{success: false, error: str(e)}`
- Log full tracebacks for debugging
- Don't crash on missing OpenAI key; degrade gracefully

