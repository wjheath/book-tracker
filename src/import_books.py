#!/usr/bin/env python3
"""
Quick script to import books from StoryGraph CSV export
"""
import os
import sys
import sqlite3
import csv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    # Database and CSV paths
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'books.db')
    csv_path = r'C:\Users\wjhea\Downloads\storygraph_1115.csv'
    
    # Check if CSV exists
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        sys.exit(1)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        read_date TEXT,
        status TEXT DEFAULT 'to-read'
    )
    """)
    
    # Import from CSV
    print(f"Importing books from: {csv_path}")
    count = 0
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                title = row.get('Title', '').strip()
                author = row.get('Authors', '').strip()
                status = row.get('Read Status', 'to-read').lower()
                read_date = None
                
                # Extract date from "Last Date Read" or "Dates Read"
                if status == 'read':
                    last_date_read = row.get('Last Date Read', '').strip()
                    dates_read = row.get('Dates Read', '').strip()
                    
                    # Use Last Date Read if available, otherwise extract from Dates Read range
                    if last_date_read:
                        read_date = last_date_read
                    elif dates_read and '-' in dates_read:
                        # Extract end date from range like "2025/06/02-2025/06/06"
                        read_date = dates_read.split('-')[-1]
                
                if title and author:
                    cursor.execute(
                        "INSERT INTO books (title, author, read_date, status) VALUES (?, ?, ?, ?)",
                        (title, author, read_date, status)
                    )
                    count += 1
        
        conn.commit()
        print(f"\nSuccessfully imported {count} books!")
        
        # Show imported books
        print("\nYour books:")
        cursor.execute("SELECT title, author, status FROM books")
        for book in cursor.fetchall():
            print(f"  - {book[0]} by {book[1]} [{book[2]}]")
            
    except Exception as e:
        print(f"Error importing CSV: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    main()
