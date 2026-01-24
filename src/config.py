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

# Prompt configuration
# You can customize the book suggestion prompt by editing CUSTOM_PROMPT_TEMPLATE below
# or by creating a file at prompts/book_suggestion.txt
CUSTOM_PROMPT_TEMPLATE = os.getenv('CUSTOM_PROMPT_TEMPLATE', None)

# Default prompt template (used if no custom prompt is found)
DEFAULT_PROMPT_TEMPLATE = """You are an expert book recommender. Based on the user's reading history:

{books_list}

Suggest {num_suggestions} books they would enjoy. For each:
1. Book title and author
2. A specific reason connecting to their reading history

Return as a numbered list: "1. **Title** by Author - reason"
"""

# Load custom prompt from file if it exists
PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'prompts')
CUSTOM_PROMPT_FILE = os.path.join(PROMPTS_DIR, 'book_suggestion.txt')

if os.path.exists(CUSTOM_PROMPT_FILE):
    try:
        with open(CUSTOM_PROMPT_FILE, 'r', encoding='utf-8') as f:
            CUSTOM_PROMPT_TEMPLATE = f.read().strip()
        print(f"Loaded custom prompt from {CUSTOM_PROMPT_FILE}")
    except Exception as e:
        print(f"Warning: Could not load custom prompt: {e}")