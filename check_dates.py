#!/usr/bin/env python3
import csv

csv_path = r'C:\Users\wjhea\Downloads\storygraph_1115.csv'

with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    books = [row for row in reader if row['Read Status'] == 'read'][:5]
    
print("Sample read books with dates:")
print("-" * 80)
for b in books:
    print(f"Title: {b['Title']}")
    print(f"  Last Date Read: '{b['Last Date Read']}'")
    print(f"  Dates Read: '{b['Dates Read']}'")
    print()
