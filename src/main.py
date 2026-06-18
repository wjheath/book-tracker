import os
import sys
from database import Database
from book_manager import BookManager
from llm_suggester import LLM_Suggester

def print_header():
    print("\n" + "="*50)
    print("        📚 BOOK TRACKER & SUGGESTER APP 📚")
    print("="*50)

def print_menu():
    print("\n--- Main Menu ---")
    print("1. Add Book")
    print("2. Remove Book")
    print("3. List All Books")
    print("4. List Read Books")
    print("5. List To-Read Books")
    print("6. Get Book Suggestions")
    print("7. Exit")

def main():
    # Load configuration
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'books.db')

    # Initialize LLM suggester
    try:
        llm_suggester = LLM_Suggester()
    except Exception as e:
        print(f"Warning: Could not initialize LLM suggester: {e}")
        llm_suggester = None

    print_header()
    print("Welcome to the Book Tracker App!")
    print("Your library has been loaded successfully.")

    with Database(db_path) as db:
        book_manager = BookManager(db)
        _run_menu_loop(book_manager, llm_suggester)


def _run_menu_loop(book_manager, llm_suggester):
    while True:
        print_menu()
        choice = input("\nChoose an option (1-7): ").strip()

        if choice == '1':
            print("\n--- Add Book ---")
            title = input("Enter book title: ").strip()
            author = input("Enter book author: ").strip()
            status = input("Enter status (to-read/read/currently-reading) [default: to-read]: ").strip().lower() or 'to-read'
            
            if title and author:
                book_manager.add_book(title, author, status)
                print(f"✓ Added '{title}' by {author} [{status}]")
            else:
                print("✗ Title and author are required.")

        elif choice == '2':
            print("\n--- Remove Book ---")
            title = input("Enter book title to remove: ").strip()
            if not title:
                print("✗ Title is required.")
                continue

            matches = [b for b in book_manager.list_books() if b['title'].strip().lower() == title.lower()]
            if not matches:
                print(f"✗ No book found with title '{title}'.")
            elif len(matches) == 1:
                book = matches[0]
                book_manager.remove_book(book['id'])
                print(f"✓ Removed '{book['title']}' by {book['author']}")
            else:
                print(f"Found {len(matches)} books with that title:")
                for i, b in enumerate(matches, 1):
                    print(f"{i}. {b['title']} by {b['author']} [{b['status']}]")
                pick = input("Enter number to remove (or blank to cancel): ").strip()
                if pick.isdigit() and 1 <= int(pick) <= len(matches):
                    book = matches[int(pick) - 1]
                    book_manager.remove_book(book['id'])
                    print(f"✓ Removed '{book['title']}' by {book['author']}")
                else:
                    print("Cancelled.")

        elif choice == '3':
            print("\n--- All Books ---")
            books = book_manager.list_books()
            if books:
                print(f"Total books: {len(books)}\n")
                for i, book in enumerate(books, 1):
                    status_emoji = "✓" if book['status'] == 'read' else "○" if book['status'] == 'to-read' else "▶"
                    print(f"{i}. {status_emoji} {book['title']} by {book['author']} [{book['status']}]")
            else:
                print("No books found.")

        elif choice == '4':
            print("\n--- Books You've Read ---")
            books = book_manager.list_books()
            read_books = [b for b in books if b['status'] == 'read']
            if read_books:
                print(f"Read books: {len(read_books)}\n")
                for i, book in enumerate(read_books, 1):
                    print(f"{i}. {book['title']} by {book['author']}")
            else:
                print("No read books found.")

        elif choice == '5':
            print("\n--- Books To Read ---")
            books = book_manager.list_books()
            to_read = [b for b in books if b['status'] == 'to-read']
            if to_read:
                print(f"To-read books: {len(to_read)}\n")
                for i, book in enumerate(to_read, 1):
                    print(f"{i}. {book['title']} by {book['author']}")
            else:
                print("No to-read books found.")

        elif choice == '6':
            if not llm_suggester:
                print("✗ LLM suggester is not available. Please check your OpenAI API key.")
                continue
            
            print("\n--- Getting Book Suggestions ---")
            all_books = book_manager.list_books()
            read_books = [b for b in all_books if b['status'] == 'read']
            
            if not read_books:
                print("✗ You need to have read some books to get suggestions.")
                continue
            
            print(f"Analyzing your {len(read_books)} read books...")
            print("Generating suggestions (this may take a moment)...\n")
            
            try:
                suggestions = llm_suggester.suggest_books(read_books, all_books=all_books, num_suggestions=5)
                
                if suggestions:
                    print("📖 Here are some book recommendations for you:\n")
                    for i, suggestion in enumerate(suggestions, 1):
                        title = suggestion.get('title', 'Unknown Title')
                        author = suggestion.get('author', 'Unknown Author')
                        reason = suggestion.get('reason', '')
                        
                        print(f"{i}. {title} by {author}")
                        if reason:
                            print(f"   Why: {reason}")
                        print()
                else:
                    print("✗ Could not generate suggestions.")
            except Exception as e:
                print(f"✗ Error getting suggestions: {e}")

        elif choice == '7':
            print("\nThank you for using Book Tracker! Happy reading! 📚")
            return

        else:
            print("✗ Invalid choice. Please try again.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExiting... Goodbye!")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)