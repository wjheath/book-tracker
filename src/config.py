import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data/books.db')

# OpenAI configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
# Preferred model(s). Use GPT-4o-mini as default (cost-effective), fall back to GPT-4o and GPT-3.5-turbo
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
GPT_PREFERRED_MODELS = os.getenv('GPT_PREFERRED_MODELS', 'gpt-4o-mini,gpt-4o,gpt-3.5-turbo').split(',')
OPENAI_REASONING = os.getenv('OPENAI_REASONING', 'medium')

# CSV import path (optional - used for importing books from StoryGraph/Goodreads exports)
CSV_IMPORT_PATH = os.getenv('CSV_IMPORT_PATH', '')

# Note: we don't raise immediately here so the app can run in limited dry-run mode
if not OPENAI_API_KEY:
    # The app will still run, but features requiring OpenAI will warn at runtime.
    OPENAI_API_KEY = None

DEBUG = True  # Set to False in production

# ── Prompt configuration ──────────────────────────────────────────────────────
# Prompts are managed via prompt_loader.  The DEFAULT_PROMPT_TEMPLATE below is
# the hardcoded fallback; prompts/book_suggestion.txt overrides it at runtime.
# You can also override via the CUSTOM_PROMPT_TEMPLATE environment variable.

# Minimal hardcoded fallback (the real prompt lives in prompts/book_suggestion.txt)
DEFAULT_PROMPT_TEMPLATE = """You are an expert book recommender. Based on the user's reading history:

{books_list}

Suggest {num_suggestions} books they would enjoy. For each:
1. Book title and author
2. A specific reason connecting to their reading history

Return as a numbered list: "1. **Title** by Author - reason"
"""

# Environment-variable override takes top priority (useful for Docker / CI)
CUSTOM_PROMPT_TEMPLATE = os.getenv('CUSTOM_PROMPT_TEMPLATE', None)

# If no env override, load from prompts/book_suggestion.txt via prompt_loader
if not CUSTOM_PROMPT_TEMPLATE:
    from prompt_loader import load_prompt as _load_prompt
    CUSTOM_PROMPT_TEMPLATE = _load_prompt('book_suggestion.txt', DEFAULT_PROMPT_TEMPLATE)