# Copilot Instructions for Book Tracker & Suggester

## Project Overview

**Book Tracker & Suggester** is a Python Flask web app with conversational AI-powered book recommendations. It manages a reading library in SQLite, uses LangGraph for multi-turn chat, and features a reader profile analyzer.

## Architecture

### Core Components

1. **Backend (Flask)**
   - [src/app.py](../src/app.py) - Flask API with 20+ REST endpoints
   - Routes: `/api/books`, `/api/suggestions`, `/api/chat`, `/api/stats`, `/api/profile`, `/api/import`, `/api/rejected`, admin endpoints
   - CORS enabled for frontend communication
   - All routes use `with Database(DB_PATH) as db:` pattern (context manager)

2. **Data Layer**
   - [src/database.py](../src/database.py) - SQLite wrapper with context manager support
   - Schema: `books`, `rejected_suggestions`, `conversations`, `reader_profile_cache`
   - **CRITICAL**: Always use `with Database(path) as db:` to auto-close connections
   - Never manually call `.close()` — let context manager handle it

3. **AI Recommendation Layer**
   - [src/llm_suggester.py](../src/llm_suggester.py) - LLM_Suggester with model fallback ("Feeling Lucky" feature)
   - [src/chat_engine.py](../src/chat_engine.py) - LangGraph-powered conversational recommendations
   - [src/reader_profile.py](../src/reader_profile.py) - Analyzes reading patterns (7 dimensions: genres, authors, pace, recency, series preference, etc.)

4. **Business Logic**
   - [src/book_manager.py](../src/book_manager.py) - BookManager class for CRUD operations and CSV imports

5. **Frontend (Single Page App)**
   - [src/index.html](../src/index.html) - Vanilla JS, ~2755 lines
   - **Tabs**: Library, Add Book, Book Chat (conversational AI), Feeling Lucky (quick suggestions), Import CSV, Admin (database editor)
   - CSS custom properties for theming
   - All API calls use relative URLs (`/api/*`) and data attributes for XSS safety

### Configuration & Environment

- [src/config.py](../src/config.py) - Centralized config loaded from `.env` or defaults
  - Key vars: `OPENAI_API_KEY`, `OPENAI_MODEL`, `GPT_PREFERRED_MODELS` (fallback list)
  - Default model: `gpt-4o-mini` (cost-effective)
  - Custom prompts: loads from `prompts/book_suggestion.txt` if exists, else uses `DEFAULT_PROMPT_TEMPLATE`
  - App runs in "dry-run" mode if no API key (graceful degradation)

## Critical Patterns

### Database Connection Safety (MOST IMPORTANT)
- **ALWAYS** use context manager: `with Database(DB_PATH) as db:` 
- Context manager auto-closes connection on exit (even on exceptions)
- **NEVER** call `db.close()` manually — let `__exit__` handle it
- **NEVER** create helper functions like `get_db()` that return bare db instances
- All routes in app.py follow this pattern — see any route for reference

### None-Safety in Data Access
- Database fields can be explicitly `None`, not just missing
- Use `book.get('field') or 'default'` instead of `book.get('field', 'default')`
- `response.content` from LLM can be `None` — always check before calling `.strip()`
- Pattern: `content = response.content if response.content is not None else ''`

### Graceful Degradation / Dry-Run Mode
- If `OPENAI_API_KEY` is missing, LLM features are disabled but the app still runs
- See [src/llm_suggester.py:31-39](../src/llm_suggester.py#L31-L39) - `if not self.api_key: self.client = None`
- Chat engine also checks: [src/chat_engine.py:243-248](../src/chat_engine.py#L243-L248)
- **When modifying**: Preserve this pattern for robustness; don't assume API key exists

### Model Fallback Strategy
- `OPENAI_MODEL` is primary choice (default: `gpt-4o-mini`)
- If model unavailable, tries models in `GPT_PREFERRED_MODELS` list
- Current list: `gpt-4o-mini,gpt-4o,gpt-3.5-turbo`
- **When adding features**: Respect this fallback chain; don't hard-code model names

### Security & XSS Prevention
- **NEVER** use inline event handlers with user data: `onclick="func('${userInput}')"`
- **ALWAYS** use data attributes: `<button data-title="${safe}" onclick="func(this)">`
- Frontend has `escapeHtml()` utility — use it on all user-generated content
- Example: [src/index.html:2646-2654](../src/index.html#L2646-L2654) (chat suggestion cards)

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
2. [src/app.py](../src/app.py#L91-L103) validates & calls `BookManager.add_book()`
3. BookManager executes `INSERT` via Database
4. Return JSON: `{success: bool, book: {...}, error?: string}`

### Get Suggestions Flow
1. Frontend POST `/api/suggestions` with `{count: 3|5|10}`
2. [src/app.py](../src/app.py#L266-L297) retrieves read books, builds prompt
3. LLM_Suggester formats books list, calls OpenAI API
4. Parse response, return list of `{title, author, reason}`
5. If API fails or key missing, return empty list (no error thrown)

### Conversational Chat Flow
1. Frontend POST `/api/chat` with `{message, conversation_id?}`
2. [src/app.py](../src/app.py#L516-L572) loads conversation state from DB
3. BookChatEngine processes message through LangGraph state machine:
   - Classify intent → Check guardrails → Route to appropriate handler
   - Handlers: context gathering, recommendations, library queries, casual chat
4. Save conversation state (messages, gathered_preferences) back to DB
5. Return `{response, suggestions, conversation_id, intent}`

### Database Schema
```sql
CREATE TABLE books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    read_date TEXT,
    status TEXT DEFAULT 'to-read',
    cover_url TEXT,
    genre TEXT,
    date_added TEXT
);

CREATE TABLE rejected_suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    rejected_date TEXT,
    reason TEXT
);

CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    title TEXT,
    messages TEXT DEFAULT '[]',
    gathered_preferences TEXT DEFAULT '{}',
    is_active INTEGER DEFAULT 1
);

CREATE TABLE reader_profile_cache (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    profile_data TEXT,
    built_at TEXT,
    book_count INTEGER
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
3. **Database Context**: Always use `with Database(DB_PATH) as db:` pattern (never manual close)
4. **None Safety**: Use `value or 'default'` for database fields that might be None
5. **LLM Response Safety**: Always check `response.content if response.content is not None else ''`
6. **Path Resolution**: Use `os.path.dirname(__file__)` for relative paths; use `os.path.join()` for portability
7. **Constants**: Centralize in `config.py`; use environment variables for deployment

## Key Files Quick Reference

| File | Purpose | Key Functions |
|------|---------|---|
| [src/app.py](../src/app.py) | Flask API | All `/api/*` routes (20+ endpoints) |
| [src/database.py](../src/database.py) | SQLite wrapper | `__enter__`, `__exit__`, `fetch_all()`, `execute_query()` |
| [src/book_manager.py](../src/book_manager.py) | Book CRUD | `add_book()`, `remove_book()`, `list_books()`, `import_from_csv()` |
| [src/llm_suggester.py](../src/llm_suggester.py) | Quick AI suggestions | `suggest_books()`, model fallback, prompt rendering |
| [src/chat_engine.py](../src/chat_engine.py) | LangGraph chat | `chat()`, intent classification, LangGraph nodes |
| [src/reader_profile.py](../src/reader_profile.py) | Profile analyzer | `build()`, `get_prompt_context()`, 7-dimension analysis |
| [src/config.py](../src/config.py) | Configuration | Environment loading, defaults, prompt file resolution |
| [src/index.html](../src/index.html) | Frontend SPA | 6 tabs, chat UI, admin mode, forms, API calls |

## Common Tasks

### Add a New Book Status
1. Update status validation in [src/app.py](../src/app.py#L75-L80)
2. Update stats calculation in [src/app.py](../src/app.py#L48-L52)
3. Update frontend filter buttons in [src/index.html](../src/index.html#L400+)

### Customize AI Prompt
- Edit [prompts/book_suggestion.txt](../prompts/book_suggestion.txt) or set `CUSTOM_PROMPT_TEMPLATE` in `.env`
- Format uses `{books_list}` and `{num_suggestions}` placeholders

### Add a New Chat Intent
1. Add intent to `INTENT_CLASSIFIER_PROMPT` in [src/chat_engine.py](../src/chat_engine.py)
2. Create handler node function (e.g., `_handle_new_intent`)
3. Add node to graph in `_build_graph()`
4. Update routing logic in `_route_after_guardrails()`

### Handle API Errors
- Try/catch blocks return `{success: false, error: str(e)}`
- Log full tracebacks for debugging
- Don't crash on missing OpenAI key; degrade gracefully

### Working with Database Fields
- Always check for None: `field = book.get('field') or 'default'`
- Never use `.get('field', 'default')` alone (doesn't catch explicit None)
- Example: `title = book.get('title') or 'Untitled'`

