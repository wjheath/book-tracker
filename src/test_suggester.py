#!/usr/bin/env python3
"""
Test script to verify the LLM suggester works
"""
import os
import sys
import sqlite3

# Add to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import Database
from book_manager import BookManager
from llm_suggester import LLM_Suggester

def main():
    print("Testing Book Suggester...\n")
    
    # Initialize database
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'books.db')
    db = Database(db_path)
    db.connect()
    
    # Initialize book manager
    book_manager = BookManager(db)
    
    # Get read books
    books = book_manager.list_books()
    read_books = [b for b in books if b['status'] == 'read']
    
    print(f"Found {len(read_books)} read books")
    print(f"Sample books: {', '.join([b['title'] for b in read_books[:3]])}\n")
    
    # Initialize and test LLM suggester
    try:
        print("Initializing LLM Suggester...")
        llm_suggester = LLM_Suggester()
        print("✓ LLM Suggester initialized\n")
        
        print("Getting book suggestions (this may take a moment)...\n")
        suggestions = llm_suggester.suggest_books(read_books[:10], num_suggestions=3)
        
        if suggestions:
            print("✓ Suggestions received!\n")
            print("📖 Book Recommendations:\n")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"{i}. {suggestion.get('title', 'Unknown')} by {suggestion.get('author', 'Unknown')}")
                if 'reason' in suggestion:
                    print(f"   Reason: {suggestion['reason']}\n")
        else:
            print("✗ No suggestions generated")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    main()
