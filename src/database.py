class Database:
    def __init__(self, db_file):
        self.db_file = db_file
        self.connection = None

    def __enter__(self):
        """Support 'with Database(path) as db:' pattern to avoid connection leaks."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False  # Don't suppress exceptions

    def connect(self):
        import sqlite3
        self.connection = sqlite3.connect(self.db_file)
        self.create_table()

    def create_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            read_date TEXT,
            status TEXT DEFAULT 'to-read',
            cover_url TEXT,
            genre TEXT,
            date_added TEXT
        );
        """
        self.execute_query(query)
        
        # Create rejected_suggestions table for thumbs-down books
        rejected_query = """
        CREATE TABLE IF NOT EXISTS rejected_suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            rejected_date TEXT,
            reason TEXT
        );
        """
        self.execute_query(rejected_query)

        # Conversation memory tables for chat engine
        conversations_query = """
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            title TEXT,
            messages TEXT DEFAULT '[]',
            gathered_preferences TEXT DEFAULT '{}',
            is_active INTEGER DEFAULT 1
        );
        """
        self.execute_query(conversations_query)

        # Reader profile cache (rebuilt periodically)
        profile_query = """
        CREATE TABLE IF NOT EXISTS reader_profile_cache (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            profile_data TEXT,
            built_at TEXT,
            book_count INTEGER
        );
        """
        self.execute_query(profile_query)
        
        # Add columns if they don't exist (for existing databases)
        migrations = [
            "ALTER TABLE books ADD COLUMN cover_url TEXT",
            "ALTER TABLE books ADD COLUMN genre TEXT",
            "ALTER TABLE books ADD COLUMN date_added TEXT"
        ]
        for migration in migrations:
            try:
                self.execute_query(migration)
            except:
                pass  # Column already exists

    def fetch_all(self, query, parameters=()):
        cursor = self.connection.cursor()
        cursor.execute(query, parameters)
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return results

    def execute_query(self, query, parameters=()):
        cursor = self.connection.cursor()
        cursor.execute(query, parameters)
        self.connection.commit()
        return cursor

    def close(self):
        if self.connection:
            self.connection.close()