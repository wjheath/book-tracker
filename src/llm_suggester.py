import os
import sys
import time
import traceback
from typing import List, Dict

# Use the official OpenAI client (2.x) quickstart pattern
try:
    from openai import OpenAI
except Exception:
    OpenAI = None

# Add project src to path so config can be imported when running from root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    OPENAI_API_KEY, OPENAI_MODEL, OPENAI_REASONING, GPT_PREFERRED_MODELS,
    CUSTOM_PROMPT_TEMPLATE, DEFAULT_PROMPT_TEMPLATE
)


class LLM_Suggester:
    """LLM-based book suggester with model fallback and dry-run mode.

    Behavior:
    - If no API key is present, operates in dry-run mode and returns empty suggestions.
    - Attempts to use the configured `OPENAI_MODEL`. If the model is unavailable,
      it will try models from `GPT_PREFERRED_MODELS` in order.
    """

    def __init__(self):
        self.api_key = OPENAI_API_KEY
        self.preferred_models = GPT_PREFERRED_MODELS or [OPENAI_MODEL]
        self.reasoning = OPENAI_REASONING
        
        # Use custom prompt template if available, otherwise use default
        self.prompt_template = CUSTOM_PROMPT_TEMPLATE or DEFAULT_PROMPT_TEMPLATE

        if not self.api_key:
            # Dry-run: allow the app to run without OpenAI access.
            print("Warning: OPENAI_API_KEY not set — LLM features are disabled (dry-run).")
            self.client = None
            self.model = None
            return

        if OpenAI is None:
            raise RuntimeError("OpenAI client library not installed. Run: pip install openai")

        # Initialize client (the 2.x client takes api_key in constructor)
        self.client = OpenAI(api_key=self.api_key)
        self.model = OPENAI_MODEL

    def _build_prompt(self, books_list: str, num_suggestions: int, all_titles: str = "", to_read_list: str = "") -> str:
        """Build the prompt for book suggestions using the configured template.
        
        Args:
            books_list: Formatted list of books the user has read (recent 50)
            num_suggestions: Number of suggestions to request
            all_titles: Simple list of all titles to avoid suggesting
            to_read_list: List of books on the user's to-read list for reference
            
        Returns:
            Formatted prompt string
        """
        prompt = self.prompt_template.format(
            books_list=books_list,
            num_suggestions=num_suggestions
        )
        
        # Add context about to-read books - can be recommended if perfect fit
        if to_read_list:
            prompt += f"\n\nThe user's 'TO-READ' list (may suggest 1-2 if they match current interests):\n{to_read_list}"
        
        # Add context about books to avoid if available
        if all_titles:
            prompt += f"\n\nAll books in their library (for reference, already read):\n{all_titles}"
        
        return prompt

    def _call_model(self, prompt: str, model: str, max_tokens: int = 800) -> str:
        """Call the OpenAI chat completions endpoint (client.chat.completions.create).

        Returns the text content on success or raises the underlying exception.
        """
        # Use the modern 2.x client interface. Some models (newer ones) expect
        # 'max_completion_tokens' instead of 'max_tokens'. Try with max_tokens
        # first, and if the API rejects that parameter, retry with the alternative.
        try:
            resp = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=max_tokens,
            )
        except Exception as e:
            msg = str(e)
            # If the error indicates max_tokens is unsupported, retry with the other name
            if 'max_tokens' in msg and 'max_completion_tokens' in msg or 'unsupported_parameter' in msg or 'max_tokens' in msg.lower():
                try:
                    resp = self.client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.7,
                        max_completion_tokens=max_tokens,
                    )
                except Exception:
                    # re-raise the original for visibility
                    raise
            else:
                raise

        # Response shape: resp.choices[0].message.content
        content = resp.choices[0].message.content
        return content

    def suggest_books(self, reading_history: List[Dict], all_books: List[Dict] = None, num_suggestions: int = 5) -> List[Dict]:
        if not reading_history:
            return []

        if not self.client:
            print("LLM disabled (no API key). Returning no suggestions.")
            return []

        # Prepare prompt from reading history (use up to 50 recent books for better context)
        # Include dates if available for temporal context
        books_list = ""
        for b in reading_history[:50]:
            title = b.get('title', 'Unknown')
            author = b.get('author', 'Unknown')
            read_date = b.get('read_date', '')
            
            if read_date:
                books_list += f"- {title} by {author} (read {read_date})\n"
            else:
                books_list += f"- {title} by {author}\n"
        
        # Extract to-read books for context (can be recommended if perfect match)
        to_read_list = ""
        if all_books:
            to_read_books = [b for b in all_books if b.get('status') == 'to-read']
            if to_read_books:
                for b in to_read_books[:30]:  # Include top 30 from to-read list
                    title = b.get('title', 'Unknown')
                    author = b.get('author', 'Unknown')
                    to_read_list += f"- {title} by {author}\n"
        
        # Prepare list of all titles for reference
        avoid_list = ""
        if all_books:
            all_titles = [b.get('title', 'Unknown') for b in all_books]
            avoid_list = "\n".join([f"- {t}" for t in all_titles[:100]])  # First 100 titles
        
        # Format prompt using template
        prompt = self._build_prompt(books_list, num_suggestions, avoid_list, to_read_list)

        last_error = None
        for candidate in self.preferred_models:
            try:
                print(f"Trying model: {candidate}")
                text = self._call_model(prompt, model=candidate)
                suggestions = self.parse_suggestions(text)
                print(f"[OK] Got {len(suggestions)} suggestions from {candidate}")
                return suggestions
            except Exception as e:
                last_error = e
                print(f"Model {candidate} failed: {e}")
                print(f"Traceback: {traceback.format_exc()}")
                # brief backoff before trying next model
                time.sleep(0.5)

        # If we reach here, all models failed
        print("All preferred models failed to produce a response.")
        if last_error:
            print(f"Last error: {last_error}")
        return []

    def parse_suggestions(self, text: str) -> List[Dict]:
        """Parse a numbered-list response into structured suggestions.
        
        Handles various formats:
        - "1. Title by Author - reason"
        - "1. **Title** – Author" (en-dash is U+2013)
        - "1. **Title** • Author"
        - "1. Title\n   Author: ...\n   Reason: ..."
        """
        results: List[Dict] = []
        if not text:
            return results

        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        current: Dict = {}

        for ln in lines:
            # Start of a numbered item (e.g., "1. something")
            if ln and ln[0].isdigit() and '.' in ln:
                # flush previous
                if current and 'title' in current:
                    results.append(current)
                    current = {}
                
                # take content after the first dot
                content = ln.split('.', 1)[1].strip()
                
                # Check for "[Already in to-read list]" notation
                is_to_read = "[already in to-read list]" in content.lower()
                if is_to_read:
                    content = content.replace("[Already in to-read list]", "").replace("[already in to-read list]", "").strip()
                
                # Remove markdown bold/italic markers
                content = content.replace('**', '').replace('*', '')
                
                # Try various separators: ' by ', ' – ' (en-dash U+2013), ' • ', ' - '
                title = None
                author = None
                
                # Try en-dash first (most common with GPT-5.1)
                if '\u2013' in content:  # en-dash
                    parts = content.split('\u2013', 1)
                    if len(parts) == 2:
                        title, author = parts[0].strip(), parts[1].strip()
                elif ' by ' in content:
                    title, author = content.rsplit(' by ', 1)
                elif ' • ' in content:
                    title, author = content.rsplit(' • ', 1)
                elif ' - ' in content and content.count(' - ') == 1:
                    parts = content.split(' - ', 1)
                    if len(parts) == 2 and len(parts[1]) < 50:  # author names usually short
                        title, author = parts
                
                if title:
                    current['title'] = title.strip()
                    if author:
                        current['author'] = author.strip()
                    if is_to_read:
                        current['in_to_read_list'] = True
                else:
                    current['title'] = content.strip()
                    if is_to_read:
                        current['in_to_read_list'] = True
            else:
                # continuation or metadata line
                low = ln.lower()
                
                # Look for author info on a separate line
                if 'author' in low and ':' in ln and 'author' not in current:
                    author_val = ln.split(':', 1)[1].strip()
                    current['author'] = author_val
                # Look for reason line
                elif any(w in low for w in ['because', 'reason:', 'why:', 'recomm']):
                    reason_val = ln
                    if ':' in ln:
                        reason_val = ln.split(':', 1)[1].strip()
                    current.setdefault('reason', reason_val)
                # Try to parse title and author if on same line but separated by delimiter
                elif '\u2013' in ln and 'title' in current and 'author' not in current:
                    # en-dash separator
                    _, author = ln.split('\u2013', 1)
                    current['author'] = author.strip()
                elif ' by ' in ln and 'title' in current and 'author' not in current:
                    _, author = ln.rsplit(' by ', 1)
                    current['author'] = author.strip()
                elif ' • ' in ln and 'title' in current and 'author' not in current:
                    _, author = ln.rsplit(' • ', 1)
                    current['author'] = author.strip()

        if current and 'title' in current:
            results.append(current)
        return results
