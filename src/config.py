import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data/books.db')

# OpenAI configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
# Preferred model(s). Try GPT-5.1 first, then fall back to known available models.
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-5.1')
GPT_PREFERRED_MODELS = os.getenv('GPT_PREFERRED_MODELS', 'gpt-5.1,gpt-5-mini,gpt-3.5-turbo').split(',')
OPENAI_REASONING = os.getenv('OPENAI_REASONING', 'medium')

# CSV import path
CSV_IMPORT_PATH = os.getenv('CSV_IMPORT_PATH', 'C:\\Users\\wjhea\\Downloads\\storygraph_1115.csv')

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
DEFAULT_PROMPT_TEMPLATE = """Based on the following books the user has read:

{books_list}

Please suggest {num_suggestions} new books they might enjoy reading next. For each suggestion, provide:
1) Book title
2) Author
3) A one-sentence reason why they might enjoy it based on their reading history

Return the suggestions as a numbered list."""

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