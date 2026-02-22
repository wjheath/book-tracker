"""
Prompt Loader — Single source of truth for loading prompt templates.

Priority order:
  1. prompts/<filename> on disk  (editable without touching code)
  2. Hardcoded default string     (always available as fallback)

Usage:
    from prompt_loader import load_prompt

    MY_PROMPT = load_prompt('my_prompt.txt', _DEFAULT_MY_PROMPT)

All prompt files live in the top-level prompts/ directory so they are
easy to find, diff, and version-control independently of the Python source.
"""

import os

# One level up from src/ → project root, then into prompts/
PROMPTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'prompts'
)


def load_prompt(filename: str, default: str) -> str:
    """Load a prompt template from the prompts/ directory.

    Args:
        filename: Filename inside prompts/ (e.g. 'chat_guardrails.txt').
        default:  Verbatim fallback if the file is absent or unreadable.

    Returns:
        Prompt string — file content when available, otherwise ``default``.
    """
    filepath = os.path.join(PROMPTS_DIR, filename)
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as fh:
                content = fh.read().strip()
            if content:
                return content
        except Exception as exc:  # pragma: no cover
            print(f"Warning: could not load prompt '{filename}': {exc}")
    return default


def list_prompts() -> list:
    """Return a sorted list of all .txt files currently in the prompts/ directory."""
    if not os.path.isdir(PROMPTS_DIR):
        return []
    return sorted(
        f for f in os.listdir(PROMPTS_DIR)
        if f.endswith('.txt')
    )
