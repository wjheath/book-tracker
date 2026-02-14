"""
Reader DNA Profile — Analyzes a user's reading history to build a rich preference profile.

This goes beyond simple "you read X" analysis. It detects:
- Genre distribution & favorites
- Author loyalty and discovery patterns
- Reading pace & velocity
- Thematic preferences (themes, moods, complexity)
- Series vs standalone preferences
- Recency-weighted interests (what they're into NOW vs historically)
"""

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple


class ReaderProfile:
    """Builds and maintains a comprehensive reader preference profile."""

    # Known genre keywords for lightweight genre inference when genre field is empty
    GENRE_HINTS = {
        'fantasy': ['magic', 'dragon', 'throne', 'kingdom', 'sword', 'quest', 'wizard', 'elf', 'ring'],
        'sci-fi': ['space', 'star', 'galaxy', 'robot', 'android', 'mars', 'alien', 'future', 'cyber'],
        'mystery': ['murder', 'detective', 'crime', 'suspect', 'clue', 'mystery', 'investigation'],
        'thriller': ['spy', 'assassin', 'conspiracy', 'chase', 'danger', 'hunt', 'secret'],
        'romance': ['love', 'heart', 'kiss', 'passion', 'desire', 'wedding', 'bride'],
        'horror': ['ghost', 'haunted', 'dark', 'nightmare', 'dead', 'blood', 'fear', 'terror'],
        'historical': ['war', 'empire', 'king', 'queen', 'century', 'ancient', 'medieval', 'colonial'],
        'literary fiction': ['life', 'story', 'memoir', 'journey', 'truth', 'beauty'],
        'non-fiction': ['how', 'why', 'history', 'science', 'guide', 'biography', 'autobiography'],
        'dystopian': ['dystopia', 'rebellion', 'control', 'society', 'government', 'surveillance'],
        'young adult': ['school', 'teen', 'coming of age', 'growing up'],
    }

    def __init__(self, books: List[Dict], all_books: Optional[List[Dict]] = None):
        """
        Args:
            books: List of read books (dicts with title, author, status, read_date, genre, etc.)
            all_books: Complete library including to-read and currently-reading
        """
        self.read_books = [b for b in books if b.get('status') == 'read']
        self.all_books = all_books or books
        self.to_read = [b for b in self.all_books if b.get('status') == 'to-read']
        self.currently_reading = [b for b in self.all_books if b.get('status') == 'currently-reading']
        self._profile: Optional[Dict] = None

    def build(self) -> Dict:
        """Build the full reader profile. Returns a dict with all analysis dimensions."""
        if self._profile:
            return self._profile

        self._profile = {
            'summary': self._build_summary(),
            'genre_distribution': self._analyze_genres(),
            'author_analysis': self._analyze_authors(),
            'reading_pace': self._analyze_pace(),
            'recency_profile': self._analyze_recency(),
            'series_preference': self._analyze_series(),
            'library_stats': self._library_stats(),
        }
        return self._profile

    def get_prompt_context(self) -> str:
        """Return a formatted string suitable for injecting into an LLM prompt."""
        profile = self.build()

        sections = []

        # Summary
        sections.append(f"## Reader Profile Summary\n{profile['summary']}")

        # Genre distribution
        genres = profile['genre_distribution']
        if genres.get('distribution'):
            genre_lines = [f"  - {g}: {pct:.0f}% ({c} books)" for g, c, pct in genres['distribution'][:8]]
            sections.append(f"## Genre Preferences\n" + "\n".join(genre_lines))
            if genres.get('top_genre'):
                sections.append(f"Primary genre: {genres['top_genre']}")

        # Author loyalty
        authors = profile['author_analysis']
        if authors.get('favorite_authors'):
            fav_lines = [f"  - {a} ({c} books)" for a, c in authors['favorite_authors'][:5]]
            sections.append(f"## Favorite Authors\n" + "\n".join(fav_lines))
        if authors.get('one_hit_authors_pct') is not None:
            sections.append(f"Discovery tendency: {authors['one_hit_authors_pct']:.0f}% of authors read only once")

        # Recency
        recency = profile['recency_profile']
        if recency.get('recent_authors'):
            sections.append(f"## Recent Interests (last 5 books)\nAuthors: {', '.join(recency['recent_authors'][:5])}")
        if recency.get('recent_genres'):
            sections.append(f"Recent genres: {', '.join(recency['recent_genres'][:5])}")

        # Reading pace
        pace = profile['reading_pace']
        if pace.get('description'):
            sections.append(f"## Reading Pace\n{pace['description']}")

        # Series preference
        series = profile['series_preference']
        if series.get('description'):
            sections.append(f"## Series vs Standalone\n{series['description']}")
        if series.get('active_series'):
            active = [f"  - {s['author']}: {', '.join(s['titles'][:4])}" for s in series['active_series'][:3]]
            sections.append(f"Active series (likely reading):\n" + "\n".join(active))

        return "\n\n".join(sections)

    # ─── Internal Analysis Methods ───────────────────────────────────────

    def _build_summary(self) -> str:
        total = len(self.read_books)
        if total == 0:
            return "New reader — no books read yet."
        
        lines = [f"Has read {total} books."]
        
        if self.to_read:
            lines.append(f"{len(self.to_read)} books on their to-read list.")
        if self.currently_reading:
            titles = [b.get('title', '') for b in self.currently_reading]
            lines.append(f"Currently reading: {', '.join(titles)}")
        
        return " ".join(lines)

    def _analyze_genres(self) -> Dict:
        """Analyze genre distribution from explicit genre fields + title-based inference."""
        genre_counter: Counter = Counter()

        for book in self.read_books:
            genre = book.get('genre', '').strip().lower()
            if genre:
                # Normalize multi-genre entries
                for g in genre.replace('/', ',').split(','):
                    g = g.strip()
                    if g:
                        genre_counter[g] += 1
            else:
                # Infer genre from title
                inferred = self._infer_genre(book.get('title', ''))
                if inferred:
                    genre_counter[inferred] += 1

        total = sum(genre_counter.values()) or 1
        distribution = [(genre, count, (count / total) * 100) 
                        for genre, count in genre_counter.most_common()]

        return {
            'distribution': distribution,
            'top_genre': distribution[0][0] if distribution else None,
            'diversity_score': len(genre_counter) / max(total, 1),  # Higher = more diverse reader
        }

    def _analyze_authors(self) -> Dict:
        """Analyze author reading patterns — loyalty, favorites, discovery tendency."""
        author_counter: Counter = Counter()
        author_books: Dict[str, List[str]] = defaultdict(list)

        for book in self.read_books:
            author = book.get('author', 'Unknown').strip()
            author_counter[author] += 1
            author_books[author].append(book.get('title', ''))

        total_authors = len(author_counter)
        one_hit = sum(1 for c in author_counter.values() if c == 1)

        favorite_authors = [(a, c) for a, c in author_counter.most_common(10) if c >= 2]

        return {
            'total_unique_authors': total_authors,
            'favorite_authors': favorite_authors,
            'author_books': dict(author_books),
            'one_hit_authors_pct': (one_hit / total_authors * 100) if total_authors else 0,
            'loyalty_score': 1 - (one_hit / total_authors) if total_authors else 0,  # Higher = more loyal
        }

    def _analyze_pace(self) -> Dict:
        """Analyze reading pace/velocity from dated reads."""
        dated = []
        for book in self.read_books:
            rd = book.get('read_date', '')
            if rd:
                parsed = self._parse_date(rd)
                if parsed:
                    dated.append(parsed)

        if len(dated) < 2:
            return {'description': 'Not enough dated reads to determine pace.', 'books_per_month': None}

        dated.sort()
        span_days = (dated[-1] - dated[0]).days
        if span_days <= 0:
            return {'description': 'All books read on the same date.', 'books_per_month': None}

        books_per_month = len(dated) / (span_days / 30.0)

        if books_per_month >= 8:
            desc = f"Voracious reader — ~{books_per_month:.1f} books/month"
        elif books_per_month >= 4:
            desc = f"Heavy reader — ~{books_per_month:.1f} books/month"
        elif books_per_month >= 2:
            desc = f"Steady reader — ~{books_per_month:.1f} books/month"
        elif books_per_month >= 1:
            desc = f"Moderate reader — ~{books_per_month:.1f} books/month"
        else:
            desc = f"Casual reader — ~{books_per_month:.1f} books/month"

        return {'description': desc, 'books_per_month': round(books_per_month, 1)}

    def _analyze_recency(self) -> Dict:
        """Analyze what the reader is into RIGHT NOW based on recent reads."""
        # Sort by read_date descending, fall back to id descending
        sorted_books = sorted(
            self.read_books,
            key=lambda b: b.get('read_date', '') or '',
            reverse=True
        )

        recent = sorted_books[:5]
        recent_authors = list(dict.fromkeys(b.get('author', '') for b in recent))
        recent_genres = []
        for b in recent:
            g = b.get('genre', '').strip()
            if g and g not in recent_genres:
                recent_genres.append(g)
            elif not g:
                inferred = self._infer_genre(b.get('title', ''))
                if inferred and inferred not in recent_genres:
                    recent_genres.append(inferred)

        recent_titles = [b.get('title', '') for b in recent]

        return {
            'recent_books': recent_titles,
            'recent_authors': recent_authors,
            'recent_genres': recent_genres,
        }

    def _analyze_series(self) -> Dict:
        """Detect series reading patterns."""
        author_books: Dict[str, List[str]] = defaultdict(list)
        for book in self.read_books:
            author = book.get('author', 'Unknown').strip()
            author_books[author].append(book.get('title', ''))

        multi_book_authors = {a: titles for a, titles in author_books.items() if len(titles) >= 2}

        if not multi_book_authors:
            return {
                'description': 'Mostly reads standalone books or single books per author.',
                'prefers_series': False,
                'active_series': [],
            }

        series_pct = len(multi_book_authors) / len(author_books) * 100 if author_books else 0
        active_series = [
            {'author': a, 'titles': t, 'count': len(t)}
            for a, t in sorted(multi_book_authors.items(), key=lambda x: len(x[1]), reverse=True)
        ]

        if series_pct > 40:
            desc = f"Strong series reader — {series_pct:.0f}% of authors have multiple books read."
        elif series_pct > 20:
            desc = f"Mixed preference — reads both series and standalones ({series_pct:.0f}% multi-book authors)."
        else:
            desc = f"Prefers standalone books — only {series_pct:.0f}% of authors have multiple books."

        return {
            'description': desc,
            'prefers_series': series_pct > 30,
            'active_series': active_series,
        }

    def _library_stats(self) -> Dict:
        return {
            'total_read': len(self.read_books),
            'total_to_read': len(self.to_read),
            'total_currently_reading': len(self.currently_reading),
            'total_library': len(self.all_books),
        }

    # ─── Helpers ─────────────────────────────────────────────────────────

    def _infer_genre(self, title: str) -> Optional[str]:
        """Lightweight genre inference from title keywords."""
        title_lower = title.lower()
        for genre, keywords in self.GENRE_HINTS.items():
            if any(kw in title_lower for kw in keywords):
                return genre
        return None

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Try multiple date formats."""
        formats = [
            '%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y', '%m/%d/%y',
            '%d/%m/%Y', '%B %d, %Y', '%b %d, %Y',
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except (ValueError, AttributeError):
                continue
        return None
