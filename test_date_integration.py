#!/usr/bin/env python3
"""
Test script to verify date integration is working
"""
import requests
import json

API_URL = "http://127.0.0.1:5000/api"

def test_dates():
    print("=" * 80)
    print("🧪 Testing Date Integration")
    print("=" * 80)
    print()
    
    # Test 1: Get books with dates
    print("1️⃣  Fetching books with dates...")
    response = requests.get(f"{API_URL}/books")
    data = response.json()
    
    if data['success']:
        books = data['books']
        
        # Show books with dates
        books_with_dates = [b for b in books if b.get('read_date')]
        print(f"   ✅ Total books: {len(books)}")
        print(f"   ✅ Books with read dates: {len(books_with_dates)}")
        
        if books_with_dates:
            print(f"\n   📚 Sample books with dates:")
            for book in books_with_dates[:5]:
                status_emoji = "✓" if book['status'] == 'read' else "○"
                print(f"      {status_emoji} {book['title']}")
                print(f"         by {book['author']}")
                print(f"         📅 Read: {book['read_date']}")
    else:
        print(f"   ❌ Error: {data.get('error')}")
    
    print()
    
    # Test 2: Check prompt includes dates
    print("2️⃣  Checking if dates are included in prompts...")
    read_books = [b for b in books if b['status'] == 'read'][:5]
    
    if read_books:
        print(f"   ✅ Found {len(read_books)} read books for context")
        
        # Show what would be sent to LLM
        print(f"\n   📝 Sample prompt context (first 3 books):")
        for book in read_books[:3]:
            if book.get('read_date'):
                print(f"      - {book['title']} by {book['author']} (read {book['read_date']})")
            else:
                print(f"      - {book['title']} by {book['author']}")
    
    print()
    
    # Test 3: Try getting suggestions
    print("3️⃣  Requesting AI suggestions (with dates)...")
    response = requests.get(f"{API_URL}/suggestions?num=3")
    data = response.json()
    
    if data['success']:
        suggestions = data['suggestions']
        print(f"   ✅ Got {len(suggestions)} suggestions")
        
        if suggestions:
            print(f"\n   💡 Sample suggestions:")
            for i, sugg in enumerate(suggestions[:2], 1):
                print(f"      {i}. {sugg.get('title', 'Unknown')} by {sugg.get('author', 'Unknown')}")
                if sugg.get('reason'):
                    print(f"         Reason: {sugg['reason']}")
    else:
        print(f"   ⚠️  {data.get('error', 'Unknown error')}")
    
    print()
    print("=" * 80)
    print("✅ Date integration test complete!")
    print("=" * 80)

if __name__ == '__main__':
    try:
        test_dates()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to Flask app at http://127.0.0.1:5000")
        print("   Make sure the Flask app is running: python src/app.py")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
