# Custom Prompts Guide

This directory contains customizable prompts for the book suggestion system.

## Quick Start

1. **Edit the default prompt:**
   - Open `book_suggestion.txt` and modify it however you like
   - Use `{books_list}` and `{num_suggestions}` as placeholders

2. **Run the app:**
   ```bash
   cd src
   python main.py
   ```
   The custom prompt will be automatically loaded!

## Available Placeholders

- `{books_list}` — A formatted list of books the user has read (one per line, with "- Title by Author")
- `{num_suggestions}` — The number of suggestions to return (default is 5)

## Example Custom Prompts

### Simple Focus
```
Based on these books:
{books_list}

Suggest {num_suggestions} similar books.
```

### Adventure-Focused
```
The user has read:
{books_list}

Suggest {num_suggestions} thrilling adventure novels with world-building and compelling characters.
```

### Diverse Recommendations
```
This reader loves:
{books_list}

Find {num_suggestions} completely different but still engaging books that might expand their horizons.
```

### Hidden Gems
```
The user is familiar with:
{books_list}

Recommend {num_suggestions} lesser-known but critically acclaimed books they might have missed.
```

## How It Works

1. When you run the app, it checks for `prompts/book_suggestion.txt`
2. If found, it loads that as your custom prompt
3. The prompt template is formatted with your reading history and preferences
4. The formatted prompt is sent to OpenAI's GPT model

## Reverting to Default

If you want to use the default prompt again, just delete `book_suggestion.txt` and restart the app.

## Tips

- Keep your prompt concise but specific
- The LLM responds better to clear formatting requests
- Be explicit about what format you want (e.g., "numbered list", "markdown", etc.)
- Experiment with different tones (professional, casual, creative, etc.)

See `EXAMPLES.md` for more complete examples!
