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

    def _build_prompt(self, books_list: str, num_suggestions: int, context: dict = None) -> str:
        """Build the prompt for book suggestions using the configured template.
        
        Args:
            books_list: Formatted list of books the user has read (recent reads first)
            num_suggestions: Number of suggestions to request
            context: Additional context dict with keys: all_titles, to_read_list, rejected_list, reading_patterns
            
        Returns:
            Formatted prompt string
        """
        context = context or {}
        
        prompt = self.prompt_template.format(
            books_list=books_list,
            num_suggestions=num_suggestions
        )
        
        # Add reading pattern analysis
        if context.get('reading_patterns'):
            prompt += f"\n\n## Reading Pattern Analysis\n{context['reading_patterns']}"
        
        # Add to-read list for reference
        if context.get('to_read_list'):
            prompt += f"\n\n## Books Already on Their To-Read List (DO NOT suggest these)\n{context['to_read_list']}"
        
        # Add rejected books - critical exclusion list
        if context.get('rejected_list'):
            prompt += f"\n\n## REJECTED BOOKS (NEVER suggest these - user explicitly rejected them)\n{context['rejected_list']}"
        
        # Add all library titles to avoid
        if context.get('all_titles'):
            prompt += f"\n\n## All Books Already in Library (avoid suggesting)\n{context['all_titles']}"
        
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

    def suggest_books(self, reading_history: List[Dict], all_books: List[Dict] = None, rejected_books: List[Dict] = None, num_suggestions: int = 5) -> List[Dict]:
        if not reading_history:
            return []

        if not self.client:
            print("LLM disabled (no API key). Returning no suggestions.")
            return []

        # Sort reading history by date (most recent first) if dates available
        sorted_history = sorted(
            reading_history,
            key=lambda b: b.get('read_date', '') or '',
            reverse=True
        )
        
        # Build detailed books list with recency markers
        books_list = ""
        recent_count = 0
        for i, b in enumerate(sorted_history[:50]):
            title = b.get('title', 'Unknown')
            author = b.get('author', 'Unknown')
            read_date = b.get('read_date', '')
            genre = b.get('genre', '')
            
            # Mark recent reads
            recency_marker = ""
            if i < 5:
                recency_marker = " [RECENT]"
                recent_count += 1
            elif i < 15:
                recency_marker = " [FAIRLY RECENT]"
            
            line = f"- {title} by {author}"
            if genre:
                line += f" ({genre})"
            if read_date:
                line += f" - read {read_date}"
            line += recency_marker
            books_list += line + "\n"
        
        # Analyze reading patterns
        reading_patterns = self._analyze_reading_patterns(sorted_history)
        
        # Extract to-read books
        to_read_list = ""
        if all_books:
            to_read_books = [b for b in all_books if b.get('status') == 'to-read']
            for b in to_read_books[:30]:
                title = b.get('title', 'Unknown')
                author = b.get('author', 'Unknown')
                to_read_list += f"- {title} by {author}\n"
        
        # Format rejected books
        rejected_list = ""
        if rejected_books:
            for b in rejected_books:
                title = b.get('title', 'Unknown')
                author = b.get('author', 'Unknown')
                rejected_list += f"- {title} by {author}\n"
        
        # All library titles
        all_titles = ""
        if all_books:
            titles = [b.get('title', 'Unknown') for b in all_books]
            all_titles = "\n".join([f"- {t}" for t in titles[:100]])
        
        # Build context
        context = {
            'reading_patterns': reading_patterns,
            'to_read_list': to_read_list,
            'rejected_list': rejected_list,
            'all_titles': all_titles
        }
        
        # Format prompt using template
        prompt = self._build_prompt(books_list, num_suggestions, context)

        last_error = None
        for candidate in self.preferred_models:
            try:
                print(f"Trying model: {candidate}")
                text = self._call_model(prompt, model=candidate, max_tokens=1200)
                suggestions = self.parse_suggestions(text)
                print(f"[OK] Got {len(suggestions)} suggestions from {candidate}")
                return suggestions
            except Exception as e:
                last_error = e
                print(f"Model {candidate} failed: {e}")
                print(f"Traceback: {traceback.format_exc()}")
                time.sleep(0.5)

        print("All preferred models failed to produce a response.")
        if last_error:
            print(f"Last error: {last_error}")
        return []

    def _analyze_reading_patterns(self, reading_history: List[Dict]) -> str:
        """Analyze reading patterns to provide context for suggestions."""
        if not reading_history:
            return ""
        
        patterns = []
        
        # Count authors to find favorites
        author_counts = {}
        author_books = {}  # Track book titles per author
        for b in reading_history:
            author = b.get('author', 'Unknown')
            title = b.get('title', '')
            author_counts[author] = author_counts.get(author, 0) + 1
            if author not in author_books:
                author_books[author] = []
            author_books[author].append(title)
        
        top_authors = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        if top_authors and top_authors[0][1] > 1:
            fav_authors = [f"{a} ({c} books)" for a, c in top_authors if c > 1]
            if fav_authors:
                patterns.append(f"Favorite authors: {', '.join(fav_authors)}")
        
        # Detect series reading - list multiple books by same author
        # This helps the LLM understand they've likely read series books
        series_info = []
        for author, books in author_books.items():
            if len(books) >= 2:
                book_list = ", ".join([f'"{b}"' for b in books[:5]])
                series_info.append(f"{author}: {book_list}")
        
        if series_info:
            patterns.append("Multiple books read by same author (likely series - DO NOT suggest earlier books in these series):")
            patterns.extend([f"  - {info}" for info in series_info[:5]])
        
        # Detect series reading (books by same author read in sequence)
        recent_authors = [b.get('author', '') for b in reading_history[:10]]
        author_streaks = {}
        for author in recent_authors:
            if author:
                author_streaks[author] = author_streaks.get(author, 0) + 1
        
        series_readers = [a for a, c in author_streaks.items() if c >= 2]
        if series_readers:
            patterns.append(f"Currently reading multiple books by: {', '.join(series_readers[:3])}")
        
        # Reading velocity (if dates available)
        dated_books = [b for b in reading_history if b.get('read_date')]
        if len(dated_books) >= 5:
            patterns.append(f"Active reader with {len(dated_books)} dated reads")
        
        # Recent vs historical preferences
        recent_5 = reading_history[:5]
        if recent_5:
            recent_authors_set = set(b.get('author', '') for b in recent_5)
            patterns.append(f"Recent authors: {', '.join(list(recent_authors_set)[:3])}")
        
        return "\n".join(patterns) if patterns else ""

    def parse_suggestions(self, text: str) -> List[Dict]:
        """Parse a structured response into suggestion objects.
        
        Expected format:
        1. Title by Author
        Summary: description
        Why: reason
        
        2. Title by Author
        Summary: description
        Why: reason
        """
        results: List[Dict] = []
        if not text:
            return results

        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        current: Dict = {}

        for ln in lines:
            # Start of a numbered item (e.g., "1. Title by Author")
            if ln and ln[0].isdigit() and '.' in ln[:3]:
                # Flush previous suggestion
                if current and 'title' in current:
                    results.append(current)
                    current = {}
                
                # Take content after the number and period
                content = ln.split('.', 1)[1].strip()
                
                # Remove any markdown formatting
                content = content.replace('**', '').replace('*', '').replace('_', '')
                
                # Parse "Title by Author" format
                title = None
                author = None
                
                if ' by ' in content:
                    parts = content.rsplit(' by ', 1)
                    title = parts[0].strip()
                    author = parts[1].strip()
                elif ' - ' in content:
                    parts = content.split(' - ', 1)
                    title = parts[0].strip()
                    if len(parts) > 1:
                        author = parts[1].strip()
                elif '\u2013' in content:  # en-dash
                    parts = content.split('\u2013', 1)
                    title = parts[0].strip()
                    if len(parts) > 1:
                        author = parts[1].strip()
                else:
                    title = content
                
                if title:
                    current['title'] = title
                if author:
                    current['author'] = author
                    
            # Summary line
            elif ln.lower().startswith('summary:'):
                summary = ln.split(':', 1)[1].strip()
                current['summary'] = summary
                
            # Why/Reason line
            elif ln.lower().startswith('why:') or ln.lower().startswith('reason:'):
                reason = ln.split(':', 1)[1].strip()
                current['reason'] = reason
                
            # Handle continuation of summary or reason (multi-line)
            elif current:
                # If we have a current suggestion but line doesn't match patterns
                # it might be a continuation of summary or reason
                if 'summary' in current and 'reason' not in current:
                    # Continuation of summary
                    current['summary'] += ' ' + ln
                elif 'reason' in current:
                    # Continuation of reason
                    current['reason'] += ' ' + ln

        # Don't forget the last suggestion
        if current and 'title' in current:
            results.append(current)
            
        return results
