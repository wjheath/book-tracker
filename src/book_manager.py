import csv

class BookManager:
    def __init__(self, database):
        self.database = database

    def add_book(self, title, author, status='to-read', read_date=None):
        query = "INSERT INTO books (title, author, status, read_date) VALUES (?, ?, ?, ?)"
        self.database.execute_query(query, (title, author, status, read_date))

    def remove_book(self, book_id):
        query = "DELETE FROM books WHERE id = ?"
        self.database.execute_query(query, (book_id,))

    def list_books(self):
        query = "SELECT * FROM books"
        return self.database.fetch_all(query)
    
    def import_from_csv(self, csv_path):
        """Import books from StoryGraph CSV export"""
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                count = 0
                for row in reader:
                    title = row.get('Title', '').strip()
                    author = row.get('Authors', '').strip()
                    status = row.get('Read Status', 'to-read').lower()
                    
                    if title and author:
                        self.add_book(title, author, status)
                        count += 1
                
                print(f"Successfully imported {count} books from CSV!")
                return count
        except FileNotFoundError:
            print(f"CSV file not found at {csv_path}")
            return 0
        except Exception as e:
            print(f"Error importing CSV: {e}")
            return 0