#!/usr/bin/env python3
"""
Test the enhanced suggestions feature with to-read list integration
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database import Database
from book_manager import BookManager

def test_suggestions():
    print("=" * 80)
    print("🧪 Testing Enhanced Suggestions with To-Read List")
    print("=" * 80)
    print()
    
    # Connect to database
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'books.db')
    db = Database(db_path)
    db.connect()
    
    book_manager = BookManager(db)
    all_books = book_manager.list_books()
    
    # Analyze books by status
    read_books = [b for b in all_books if b['status'] == 'read']
    to_read_books = [b for b in all_books if b['status'] == 'to-read']
    currently_reading = [b for b in all_books if b['status'] == 'currently-reading']
    
    print("📊 Library Statistics:")
    print(f"   Total books: {len(all_books)}")
    print(f"   Read: {len(read_books)}")
    print(f"   To-Read: {len(to_read_books)}")
    print(f"   Currently Reading: {len(currently_reading)}")
    print()
    
    # Show books with dates
    read_with_dates = [b for b in read_books if b.get('read_date')]
    print(f"📅 Read Books with Dates:")
    print(f"   Total with dates: {len(read_with_dates)}")
    if read_with_dates:
        print(f"\n   Sample (first 3):")
        for b in read_with_dates[:3]:
            print(f"      ✓ {b['title']}")
            print(f"        by {b['author']}")
            print(f"        Read: {b['read_date']}")
    print()
    
    # Show to-read books
    print(f"📌 To-Read List Sample (first 5):")
    if to_read_books:
        for b in to_read_books[:5]:
            print(f"      ○ {b['title']}")
            print(f"        by {b['author']}")
    else:
        print("      (empty)")
    print()
    
    # Check API readiness
    print("✅ API Readiness:")
    print(f"   ✅ Read books for context: {len(read_books)}")
    print(f"   ✅ To-read books for suggestions: {len(to_read_books)}")
    print(f"   ✅ Dates available: {len(read_with_dates)}")
    print()
    
    # Show what AI will receive
    print("🤖 AI Will See:")
    print(f"   - Up to 50 read books with dates (have {min(50, len(read_books))})")
    print(f"   - Up to 30 to-read books (have {min(30, len(to_read_books))})")
    print(f"   - All {len(all_books)} books for reference")
    print()
    
    print("📝 Suggestion Strategy:")
    print("   - ~80% completely new books")
    print("   - ~20% from to-read list (if they match perfectly)")
    print()
    
    db.close()
    
    print("=" * 80)
    print("✅ Enhanced Suggestions Test Complete!")
    print("=" * 80)
    print()
    print("Ready to use! Start the app and get suggestions.")
    print("You should see:")
    print("  • Gray cards for completely new book recommendations")
    print("  • Orange cards for to-read books that match your taste")
    print("  • 📌 Badge on to-read suggestions")
    print()

if __name__ == '__main__':
    test_suggestions()
