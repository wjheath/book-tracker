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

import json as _json
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple


class ReaderProfile:
    """Builds and maintains a comprehensive reader preference profile."""

    # ── Author → genre list (takes precedence over title keywords) ──────────
    # Covers hundreds of widely-read authors; match is done on normalised name
    # (lowercase, punctuation stripped) so "J.K. Rowling" == "jk rowling".
    AUTHOR_GENRES: Dict[str, List[str]] = {
        # Literary Fiction / Contemporary
        'haruki murakami':      ['literary fiction', 'magical realism'],
        'ben lerner':           ['literary fiction'],
        'percival everett':     ['literary fiction'],
        'kaveh akbar':          ['literary fiction', 'poetry'],
        'john williams':        ['literary fiction'],
        'oscar wilde':          ['literary fiction', 'classic'],
        'albert camus':         ['literary fiction', 'philosophy'],
        'franz kafka':          ['literary fiction', 'absurdism'],
        'gabriel garcia marquez':['literary fiction', 'magical realism'],
        'toni morrison':        ['literary fiction'],
        'cormac mccarthy':      ['literary fiction', 'western', 'horror'],
        'don delillo':          ['literary fiction'],
        'philip roth':          ['literary fiction'],
        'ian mcewan':           ['literary fiction'],
        'kazuo ishiguro':       ['literary fiction', 'science fiction'],
        'colson whitehead':     ['literary fiction', 'historical fiction'],
        'jesmyn ward':          ['literary fiction'],
        'chimamanda ngozi adichie': ['literary fiction'],
        'zadie smith':          ['literary fiction'],
        'salman rushdie':       ['literary fiction', 'magical realism'],
        'david sedaris':        ['memoir', 'humor'],
        'jr moehringer':        ['memoir', 'non-fiction'],
        'j r moehringer':       ['memoir', 'non-fiction'],
        # Fantasy
        'robin hobb':           ['fantasy'],
        'brandon sanderson':    ['fantasy'],
        'terry pratchett':      ['fantasy', 'humor'],
        'neil gaiman':          ['fantasy', 'horror'],
        'ursula k le guin':     ['fantasy', 'science fiction'],
        'ursula le guin':       ['fantasy', 'science fiction'],
        'j r r tolkien':        ['fantasy'],
        'jrr tolkien':          ['fantasy'],
        'george rr martin':     ['fantasy'],
        'george r r martin':    ['fantasy'],
        'patrick rothfuss':     ['fantasy'],
        'joe abercrombie':      ['fantasy'],
        'scott lynch':          ['fantasy'],
        'steven erikson':       ['fantasy'],
        'robert jordan':        ['fantasy'],
        'guy gavriel kay':      ['fantasy', 'historical fiction'],
        'susanna clarke':       ['fantasy', 'historical fiction'],
        'naomi novik':          ['fantasy', 'historical fiction'],
        'k j parker':           ['fantasy'],
        'terry goodkind':       ['fantasy'],
        'raymond e feist':      ['fantasy'],
        'david gemmell':        ['fantasy'],
        'michael j sullivan':   ['fantasy'],
        'christopher paolini':  ['fantasy', 'young adult'],
        'cinda williams chima': ['fantasy', 'young adult'],
        'tamora pierce':        ['fantasy', 'young adult'],
        'rick riordan':         ['fantasy', 'mythology', 'young adult'],
        'cs lewis':             ['fantasy', 'children'],
        'c s lewis':            ['fantasy', 'children'],
        'jk rowling':           ['fantasy', 'young adult'],
        'j k rowling':          ['fantasy', 'young adult'],
        'matt dinniman':        ['fantasy', 'humor'],
        'jim butcher':          ['fantasy', 'urban fantasy'],
        'ilona andrews':        ['fantasy', 'urban fantasy', 'romance'],
        'patricia briggs':      ['fantasy', 'urban fantasy'],
        'larry correia':        ['fantasy', 'urban fantasy'],
        'kevin hearne':         ['fantasy', 'urban fantasy'],
        'peter v brett':        ['fantasy'],
        'brent weeks':          ['fantasy'],
        'sam sykes':            ['fantasy'],
        'mark lawrence':        ['fantasy'],
        'michael j sulliven':   ['fantasy'],
        'will wight':           ['fantasy'],
        'andrew rowe':          ['fantasy'],
        'travis baldree':       ['fantasy', 'cozy'],
        'becky chambers':       ['science fiction', 'cozy'],
        # Horror
        'christopher buehlman': ['horror', 'fantasy'],
        'stephen king':         ['horror', 'thriller'],
        'shirley jackson':      ['horror', 'literary fiction'],
        'hp lovecraft':         ['horror'],
        'h p lovecraft':        ['horror'],
        'clive barker':         ['horror', 'fantasy'],
        'peter straub':         ['horror'],
        'paul tremblay':        ['horror'],
        'josh malerman':        ['horror', 'thriller'],
        'grady hendrix':        ['horror', 'humor'],
        'adam nevill':          ['horror'],
        'john dies at the end': ['horror', 'humor'],
        # Science Fiction
        'ted chiang':           ['science fiction'],
        'jeff vandermeer':      ['science fiction', 'weird fiction'],
        'pierce brown':         ['science fiction', 'dystopian'],
        'andy weir':            ['science fiction'],
        'kim stanley robinson': ['science fiction'],
        'ursula k leguin':      ['science fiction', 'fantasy'],
        'isaac asimov':         ['science fiction'],
        'arthur c clarke':      ['science fiction'],
        'philip k dick':        ['science fiction'],
        'kurt vonnegut':        ['science fiction', 'literary fiction'],
        'frank herbert':        ['science fiction'],
        'dan simmons':          ['science fiction', 'horror'],
        'ann leckie':           ['science fiction'],
        'n k jemisin':          ['science fiction', 'fantasy'],
        'octavia butler':       ['science fiction'],
        'cixin liu':            ['science fiction'],
        'peter watts':          ['science fiction'],
        'alastair reynolds':    ['science fiction'],
        'peter f hamilton':     ['science fiction'],
        'iain m banks':         ['science fiction'],
        # Mystery / Thriller / Crime
        'agatha christie':      ['mystery', 'classic'],
        'raymond chandler':     ['mystery', 'noir'],
        'dashiell hammett':     ['mystery', 'noir'],
        'donna tartt':          ['literary fiction', 'mystery'],
        'tana french':          ['mystery', 'literary fiction'],
        'gillian flynn':        ['thriller', 'mystery'],
        'stieg larsson':        ['thriller', 'mystery'],
        'jo nesbo':             ['thriller', 'mystery'],
        'lee child':            ['thriller'],
        'michael connelly':     ['mystery', 'thriller'],
        'john le carre':        ['thriller', 'spy'],
        'james ellroy':         ['mystery', 'noir'],
        # Historical Fiction
        'hilary mantel':        ['historical fiction', 'literary fiction'],
        'ken follett':          ['historical fiction', 'thriller'],
        'colleen mccullough':   ['historical fiction'],
        'philippa gregory':     ['historical fiction'],
        'bernard cornwell':     ['historical fiction', 'adventure'],
        'robert harris':        ['historical fiction', 'thriller'],
        # Romance
        'nora roberts':         ['romance'],
        'julia quinn':          ['romance', 'historical fiction'],
        'lisa kleypas':         ['romance', 'historical fiction'],
        # Non-fiction
        'david j silbey':       ['history', 'non-fiction'],
        'mary roach':           ['non-fiction', 'humor', 'science'],
        'bill bryson':          ['non-fiction', 'humor'],
        'malcolm gladwell':     ['non-fiction'],
        'michael lewis':        ['non-fiction'],
        'yuval noah harari':    ['non-fiction', 'history'],
        # Graphic Novel / Comics
        'rhea ewing':           ['graphic novel'],
        'art spiegelman':       ['graphic novel', 'memoir'],
        'alison bechdel':       ['graphic novel', 'memoir'],
        'craig thompson':       ['graphic novel', 'memoir'],
    }

    # ── Open Library subject → our genre vocabulary ────────────────────────
    # Checked with str.find() so "Fantasy fiction" matches "fantasy", etc.
    # Order matters: more-specific phrases must come before their substrings.
    OL_SUBJECT_MAP: List[Tuple[str, str]] = [
        ('urban fantasy',         'urban fantasy'),
        ('fantasy',               'fantasy'),
        ('magic',                 'fantasy'),
        ('wizard',                'fantasy'),
        ('dragon',                'fantasy'),
        ('fairy',                 'fantasy'),
        ('mytholog',              'fantasy'),
        ('science fiction',       'science fiction'),
        ('space opera',           'science fiction'),
        ('cyberpunk',             'science fiction'),
        ('dystopi',               'dystopian'),
        ('mystery',               'mystery'),
        ('detective',             'mystery'),
        ('crime fiction',         'mystery'),
        ('thriller',              'thriller'),
        ('suspense',              'thriller'),
        ('horror',                'horror'),
        ('ghost stori',           'horror'),
        ('occult',                'horror'),
        ('romance',               'romance'),
        ('historical fiction',    'historical fiction'),
        ('historical novel',      'historical fiction'),
        ('literary fiction',      'literary fiction'),
        ('psychological fiction',  'literary fiction'),
        ('magical realism',       'magical realism'),
        ('young adult',           'young adult'),
        ('juvenile fiction',      'young adult'),
        ('graphic novel',         'graphic novel'),
        ('comic',                 'graphic novel'),
        ('manga',                 'graphic novel'),
        ('biography',             'memoir'),
        ('autobiography',         'memoir'),
        ('memoir',                'memoir'),
        ('nonfiction',            'non-fiction'),
        ('non-fiction',           'non-fiction'),
        ('history',               'history'),
        ('poetry',                'poetry'),
        ('short stories',         'short stories'),
        ('humor',                 'humor'),
        ('satire',                'humor'),
    ]

    # ── Title keyword hints (fallback when author is not in AUTHOR_GENRES) ──
    # Intentionally broader and allows multi-genre matches.
    GENRE_HINTS: Dict[str, List[str]] = {
        'fantasy':          ['magic', 'dragon', 'throne', 'kingdom', 'sword', 'quest',
                             'wizard', 'elf', 'sorcerer', 'mage', 'ring', 'dwarv',
                             'fae', 'faerie', 'witch', 'warlock', 'dungeon', 'spell',
                             'enchant', 'mythic', 'legend', 'rune', 'orcs', 'goblin',
                             'elven', 'heroic', 'realm', 'prophecy'],
        'science fiction':  ['space', 'star ', 'galaxy', 'robot', 'android', 'mars',
                             'alien', 'future', 'cyber', 'warp', 'laser', 'quantum',
                             'clone', 'mutation', 'colony ', 'station ', 'empire ',
                             'planet', 'nebula', 'void ', 'starship', 'terraform'],
        'mystery':          ['murder', 'detective', 'crime', 'clue', 'mystery',
                             'investigation', 'case ', 'suspect', 'sleuth'],
        'thriller':         ['spy', 'assassin', 'conspiracy', 'chase', 'danger',
                             'hunt ', 'secret ', 'covert', 'tactical', 'heist'],
        'horror':           ['ghost', 'haunted', 'nightmare', 'dead ', 'blood',
                             'fear ', 'terror', 'supernatural', 'demon', 'cursed',
                             'crypt', 'macabre', 'undead'],
        'historical fiction':['war', 'empire', 'century', 'ancient', 'medieval',
                              'colonial', 'victorian', 'tudor', 'roman', 'revolution',
                              'civil war', 'world war'],
        'literary fiction': ['station', 'atocha', 'stoner', 'ruin', 'martyr'],
        'dystopian':        ['dystopia', 'rebellion', 'surveillance', 'regime',
                             'totalitarian', 'resistance '],
        'young adult':      ['chosen one', 'academy ', 'high school', 'coming of age'],
        'non-fiction':      ['biography', 'autobiography', 'memoir', 'history of',
                             'guide to', 'how to', 'the making of', 'the story of'],
        'humor':            ['absurd', 'comedy', 'funny', 'satire', 'ridiculous'],
        'magical realism':  ['miraculous', 'surreal', 'dream ', 'memory ', 'illusion'],
    }

    def __init__(self, books: List[Dict], all_books: Optional[List[Dict]] = None,
                 favorite_authors: Optional[List[str]] = None):
        """
        Args:
            books: List of read books (dicts with title, author, status, read_date, genre, etc.)
            all_books: Complete library including to-read and currently-reading
            favorite_authors: User-selected list of up to 3 favourite author names
        """
        self.read_books = [b for b in books if b.get('status') == 'read']
        self.all_books = all_books or books
        self.to_read = [b for b in self.all_books if b.get('status') == 'to-read']
        self.currently_reading = [b for b in self.all_books if b.get('status') == 'currently-reading']
        self.favorite_authors: List[str] = favorite_authors or []
        self._profile: Optional[Dict] = None
        # {book_id: genre_str} — populated by _prefetch_ol_genres during build()
        self._ol_cache: Dict[int, str] = {}

    def build(self) -> Dict:
        """Build the full reader profile. Returns a dict with all analysis dimensions."""
        if self._profile:
            return self._profile

        # Pre-populate OL genre cache for books that have no saved genre.
        # Must happen before any analysis method runs.
        self._prefetch_ol_genres(max_requests=20)

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
        """Return a formatted string suitable for injecting into an LLM prompt.

        Sections are ordered by signal strength:
          1. Recent reads (most important — current taste)
          2. Genre preference (all-time)
          3. All-time favourite authors (background context only)
          4. Reading pace
        The 'active series' block is intentionally omitted from chat context
        because a high all-time multi-book count (e.g. Robin Hobb) misleads the
        LLM into treating historical binge-reads as current interests.
        """
        profile = self.build()
        sections = []

        # ── 1. RECENCY — listed first so the LLM anchors on current taste ──
        recency = profile['recency_profile']
        entries = recency.get('recent_entries', [])
        if entries:
            entry_lines = []
            for e in entries:
                date_str = f" (read {e['read_date']})" if e['read_date'] else ''
                entry_lines.append(f"  {len(entry_lines)+1}. {e['title']} — {e['author']}{date_str}")
            genre_str = ', '.join(recency.get('recent_genres', [])[:5])
            recent_section = (
                "## Most Recently Read (use these as the PRIMARY taste signal)\n"
                + "\n".join(entry_lines)
            )
            if genre_str:
                recent_section += f"\nCurrent genre lean: {genre_str}"
            sections.append(recent_section)
        elif recency.get('recent_books'):
            # Fallback for older data without entries
            title_lines = "\n".join([f"  - {t}" for t in recency['recent_books'][:10]])
            sections.append(f"## Most Recently Read (PRIMARY taste signal)\n{title_lines}")

        # ── 2. Summary ──
        sections.append(f"## Reader Summary\n{profile['summary']}")

        # ── 3. Genre distribution (all-time, secondary context) ──
        genres = profile['genre_distribution']
        if genres.get('distribution'):
            genre_lines = [f"  - {g}: {pct:.0f}% ({c} books)" for g, c, pct in genres['distribution'][:6]]
            sections.append("## All-Time Genre Preferences (secondary context)\n" + "\n".join(genre_lines))

        # ── 4. Favourite authors ─────────────────────────────────────────────
        authors = profile['author_analysis']
        user_favs = authors.get('user_favorites', [])
        if user_favs:
            # User-selected — most reliable signal
            fav_lines = [f"  - {a}" for a in user_favs]
            sections.append(
                "## Favourite Authors (user-selected)\n" + "\n".join(fav_lines)
            )
        elif authors.get('favorite_authors'):
            # Fallback: computed by volume, clearly labelled
            fav_lines = [f"  - {a} ({c} books total)" for a, c in authors['favorite_authors'][:5]]
            sections.append(
                "## All-Time Favourite Authors (historical — high count ≠ currently reading)\n"
                + "\n".join(fav_lines)
            )

        # ── 5. Reading pace ──
        pace = profile['reading_pace']
        if pace.get('description'):
            sections.append(f"## Reading Pace\n{pace['description']}")

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
        """Analyze genre distribution.

        Priority per book: explicit DB field > AUTHOR_GENRES map > title keywords.
        A book can contribute to *multiple* genre buckets.
        """
        genre_counter: Counter = Counter()

        for book in self.read_books:
            seen: set = set()
            for g in self._get_genres_for_book(book):
                if g not in seen:
                    seen.add(g)
                    genre_counter[g] += 1

        total = sum(genre_counter.values()) or 1
        distribution = [
            (genre, count, (count / total) * 100)
            for genre, count in genre_counter.most_common()
        ]

        return {
            'distribution': distribution,
            'top_genre': distribution[0][0] if distribution else None,
            'diversity_score': len(genre_counter) / max(total, 1),
        }

    def _analyze_authors(self) -> Dict:
        """Analyze author reading patterns.

        `user_favorites` mirrors `self.favorite_authors` so callers can access
        user-selected favourites from the built profile dict.
        """
        author_counter: Counter = Counter()
        author_books: Dict[str, List[str]] = defaultdict(list)

        for book in self.read_books:
            author_raw = book.get('author') or 'Unknown'
            author = author_raw.strip()
            author_counter[author] += 1
            title = book.get('title') or 'Untitled'
            author_books[author].append(title)

        total_authors = len(author_counter)
        one_hit = sum(1 for c in author_counter.values() if c == 1)

        # Computed top authors by volume (for fallback display only)
        computed_top = [(a, c) for a, c in author_counter.most_common(10) if c >= 2]

        return {
            'total_unique_authors': total_authors,
            'favorite_authors': computed_top,       # kept for backward compat
            'user_favorites': self.favorite_authors, # user-selected (may be [])
            'author_books': dict(author_books),
            'one_hit_authors_pct': (one_hit / total_authors * 100) if total_authors else 0,
            'loyalty_score': 1 - (one_hit / total_authors) if total_authors else 0,
            # Sorted list of all authors read (for the UI picker)
            'all_read_authors': sorted(author_counter.keys()),
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
        # IMPORTANT: M/D/YYYY strings do NOT sort correctly lexicographically.
        # Always parse dates before comparing; fall back to id for undated books.
        def _recency_key(b: Dict):
            dt = self._parse_date(b.get('read_date') or '') \
                 or self._parse_date(b.get('date_added') or '')
            return (dt or datetime.min, b.get('id', 0))

        sorted_books = sorted(self.read_books, key=_recency_key, reverse=True)

        recent = sorted_books[:10]
        recent_authors = list(dict.fromkeys((b.get('author') or '') for b in recent))
        recent_genres: List[str] = []
        for b in recent:
            for g in self._get_genres_for_book(b):
                if g not in recent_genres:
                    recent_genres.append(g)

        # Rich recent-book entries: title, author, and read_date for full transparency
        recent_entries = []
        for b in recent:
            entry = {
                'title': b.get('title') or 'Untitled',
                'author': b.get('author') or 'Unknown',
                'read_date': b.get('read_date') or '',
            }
            recent_entries.append(entry)

        return {
            'recent_books': [e['title'] for e in recent_entries],  # kept for compat
            'recent_entries': recent_entries,
            'recent_authors': recent_authors,
            'recent_genres': recent_genres,
        }

    def _analyze_series(self) -> Dict:
        """Detect series reading patterns."""
        author_books: Dict[str, List[str]] = defaultdict(list)
        for book in self.read_books:
            author_raw = book.get('author') or 'Unknown'
            author = author_raw.strip()
            title = book.get('title') or 'Untitled'
            author_books[author].append(title)

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

    def _normalize_ol_subjects(self, subjects: List[str]) -> str:
        """Map a list of Open Library subject strings to our genre vocabulary."""
        seen: set = set()
        genres: List[str] = []
        for subj in subjects:
            sl = subj.lower()
            for frag, genre in self.OL_SUBJECT_MAP:
                if frag in sl and genre not in seen:
                    seen.add(genre)
                    genres.append(genre)
            if len(genres) >= 4:
                break
        return ', '.join(genres)

    def _fetch_ol_genre(self, title: str, author: str) -> str:
        """Query Open Library for a book's genre. Returns normalized genre string or ''."""
        try:
            query = urllib.parse.quote(f"{title} {author}")
            url = f"https://openlibrary.org/search.json?q={query}&limit=1&fields=subject"
            req = urllib.request.Request(url, headers={'User-Agent': 'BookSuggester/1.0'})
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = _json.loads(resp.read().decode())
            docs = data.get('docs') or []
            if docs:
                return self._normalize_ol_subjects(docs[0].get('subject') or [])
        except Exception:
            pass
        return ''

    def _prefetch_ol_genres(self, max_requests: int = 20) -> None:
        """Fetch genres from Open Library for read books that have no saved genre.

        Bounded to `max_requests` per build (most recently read books are prioritised)
        so the profile endpoint stays responsive even with large libraries.
        Results are stored in `self._ol_cache` for use by `_get_genres_for_book`.
        """
        books_needing_genre = [
            b for b in self.read_books
            if not (b.get('genre') or '').strip()
            and b.get('title')
        ]
        # Sort by recency so we enrich the most relevant books first
        def _sort_key(b):
            rd = b.get('read_date') or b.get('date_added') or ''
            if rd:
                parsed = self._parse_date(rd)
                if parsed:
                    return parsed
            return datetime.min

        books_needing_genre.sort(key=_sort_key, reverse=True)

        for book in books_needing_genre[:max_requests]:
            book_id = book.get('id')
            if book_id is None:
                continue
            genre = self._fetch_ol_genre(
                book.get('title') or '', book.get('author') or ''
            )
            self._ol_cache[book_id] = genre

    def get_ol_enriched_genres(self) -> Dict[int, str]:
        """Return {book_id: genre_str} for every book successfully enriched via Open Library.

        Call after `build()`. The app layer can use this to persist genres to the DB
        so future profile builds skip the network requests.
        """
        return {bid: g for bid, g in self._ol_cache.items() if g}

    def _get_genres_for_book(self, book: Dict) -> List[str]:
        """Return a deduplicated list of genre tags for a single book.
        Priority: explicit DB genre field > Open Library API > AUTHOR_GENRES map > title keywords.
        """
        import re as _re

        # 1. Explicit DB genre field (may have been saved by a previous OL enrichment)
        genre_raw = (book.get('genre') or '').strip().lower()
        if genre_raw:
            genres = [g.strip() for g in genre_raw.replace('/', ',').split(',') if g.strip()]
            if genres:
                return list(dict.fromkeys(genres))

        # 2. Open Library (pre-fetched into _ol_cache by _prefetch_ol_genres)
        book_id = book.get('id')
        if book_id is not None and book_id in self._ol_cache:
            ol_genre = self._ol_cache[book_id]
            if ol_genre:
                return [g.strip() for g in ol_genre.split(',') if g.strip()]

        # 3. Author map (fast offline fallback)
        author_norm = _re.sub(r'[^a-z0-9 ]', '', (book.get('author') or '').lower()).strip()
        author_genres = self.AUTHOR_GENRES.get(author_norm, [])
        if author_genres:
            return list(dict.fromkeys(author_genres))

        # 4. Title keyword fallback (multi-genre)
        title_lower = (book.get('title') or '').lower()
        matched: List[str] = []
        for genre, keywords in self.GENRE_HINTS.items():
            if any(kw in title_lower for kw in keywords):
                matched.append(genre)
        return list(dict.fromkeys(matched))

    def _infer_genre(self, title: str) -> Optional[str]:
        """Legacy single-genre title inference (returns first match only)."""
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
