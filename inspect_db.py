#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('data/books.db')
c = conn.cursor()
c.execute('SELECT title, author FROM books LIMIT 10')
rows = c.fetchall()
print(f"First 10 rows:\n")
for i, (title, author) in enumerate(rows, 1):
    print(f"{i}. Title: {repr(title)}")
    print(f"   Author: {repr(author)}\n")
conn.close()
