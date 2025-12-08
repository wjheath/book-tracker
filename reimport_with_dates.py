#!/usr/bin/env python3
"""
Re-import books from CSV with date information
This script clears the existing books table and reimports with date support
"""
import os
import sys
import sqlite3
import csv
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    # Database and CSV paths
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'books.db')
    csv_path = r'C:\Users\wjhea\Downloads\storygraph_1115.csv'
    
    # Ensure data directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Check if CSV exists
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        sys.exit(1)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table (will overwrite if exists)
    print("Creating books table...")
    cursor.execute("DROP TABLE IF EXISTS books")
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
    read_count = 0
    with_dates = 0
    
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
                        with_dates += 1
                    elif dates_read and '-' in dates_read:
                        # Extract end date from range like "2025/06/02-2025/06/06"
                        read_date = dates_read.split('-')[-1]
                        with_dates += 1
                
                if title and author:
                    cursor.execute(
                        "INSERT INTO books (title, author, read_date, status) VALUES (?, ?, ?, ?)",
                        (title, author, read_date, status)
                    )
                    count += 1
                    if status == 'read':
                        read_count += 1
        
        conn.commit()
        print(f"\n✅ Successfully imported {count} books!")
        print(f"   - {read_count} books marked as read")
        print(f"   - {with_dates} read books with date information")
        
        # Show some statistics
        cursor.execute("SELECT COUNT(*) FROM books WHERE status = 'read' AND read_date IS NOT NULL")
        dated_reads = cursor.fetchone()[0]
        print(f"   - {dated_reads} read books with read dates in database")
        
        # Show sample books with dates
        print("\n📚 Sample read books with dates:")
        cursor.execute(
            "SELECT title, author, read_date FROM books WHERE status = 'read' AND read_date IS NOT NULL LIMIT 5"
        )
        for title, author, date in cursor.fetchall():
            print(f"   - {title} by {author} (read {date})")
            
    except Exception as e:
        print(f"❌ Error importing CSV: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.close()
    
    print("\n✅ Database import complete!")

if __name__ == '__main__':
    main()
