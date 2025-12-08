#!/usr/bin/env python3
"""
Inspect database and CSV for title/author parsing issues.
Prints samples where the title contains ' by ' but the author field is empty or 'Unknown'.
"""
import os
import sqlite3
import csv
import sys

# Add project root to path
ROOT = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(ROOT, '..', 'downloads_missing.csv')
try:
    from config import CSV_IMPORT_PATH
    csv_path = CSV_IMPORT_PATH
except Exception:
    csv_path = os.path.join(os.path.expanduser('~'), 'Downloads', 'storygraph_1115.csv')

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'books.db')

print('Using DB:', DB_PATH)
print('Using CSV:', csv_path)

if not os.path.exists(DB_PATH):
    print('Database not found at', DB_PATH)
    sys.exit(1)

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

query = "SELECT id, title, author, status FROM books WHERE (author IS NULL OR trim(author)='' OR lower(author) IN ('unknown','unknown author')) AND title LIKE '% by %' LIMIT 200"
c.execute(query)
rows = c.fetchall()
print(f"Found {len(rows)} DB rows where title contains ' by ' and author is empty/unknown")
for r in rows[:50]:
    print(r)

# Now inspect the CSV for rows where Authors empty but Title contains ' by '
if not os.path.exists(csv_path):
    print('CSV not found at', csv_path)
else:
    print('\nScanning CSV for problematic rows...')
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        csv_problems = []
        for i, row in enumerate(reader, 1):
            title = (row.get('Title') or '').strip()
            authors = (row.get('Authors') or '').strip()
            if title and (' by ' in title.lower()) and not authors:
                csv_problems.append((i, title, authors))
        print(f'Found {len(csv_problems)} CSV rows where Title contains " by " and Authors is empty')
        for p in csv_problems[:50]:
            print(p)

conn.close()
print('\nDone')
