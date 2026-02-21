import csv
from datetime import datetime

class BookManager:
    def __init__(self, database):
        self.database = database

    def add_book(self, title, author, status='to-read', read_date=None, date_added=None):
        if date_added is None:
            date_added = datetime.now().strftime('%Y-%m-%d')
        query = "INSERT INTO books (title, author, status, read_date, date_added) VALUES (?, ?, ?, ?, ?)"
        self.database.execute_query(query, (title, author, status, read_date, date_added))

    def remove_book(self, book_id):
        query = "DELETE FROM books WHERE id = ?"
        self.database.execute_query(query, (book_id,))

    def list_books(self):
        query = "SELECT * FROM books"
        return self.database.fetch_all(query)
    
    def import_from_csv(self, csv_path):
        """Import books from StoryGraph CSV export.
        
        Reads: Title, Authors, Read Status, Date Read, Date Added
        StoryGraph column names are matched case-insensitively.
        """
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                # Normalise header names so we're robust to case/whitespace
                headers = {h.strip().lower(): h for h in (reader.fieldnames or [])}
                def _col(row, *candidates):
                    """Return first matching column value, or ''"""
                    for c in candidates:
                        orig = headers.get(c.lower())
                        if orig:
                            val = row.get(orig, '').strip()
                            if val:
                                return val
                    return ''

                count = 0
                for row in reader:
                    title = _col(row, 'Title')
                    author = _col(row, 'Authors')
                    status = _col(row, 'Read Status') or 'to-read'
                    read_date = _col(row, 'Date Read', 'Read Date') or None
                    date_added = _col(row, 'Date Added') or None

                    if title and author:
                        self.add_book(title, author, status.lower(), read_date, date_added)
                        count += 1

                print(f"Successfully imported {count} books from CSV!")
                return count
        except FileNotFoundError:
            print(f"CSV file not found at {csv_path}")
            return 0
        except Exception as e:
            print(f"Error importing CSV: {e}")
            return 0