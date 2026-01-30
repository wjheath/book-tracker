import os
import sys
import csv
import io
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from database import Database
from book_manager import BookManager
from llm_suggester import LLM_Suggester

# Initialize Flask app with static folder
app = Flask(__name__, static_folder=os.path.dirname(__file__), static_url_path='')
CORS(app)

# Initialize database and managers
def get_db():
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'books.db')
    db = Database(db_path)
    db.connect()
    return db

def get_book_manager():
    db = get_db()
    return BookManager(db), db

def get_llm_suggester():
    try:
        return LLM_Suggester()
    except Exception as e:
        return None

# ============== WEB UI ROUTES ==============

@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_file('index.html')

# ============== API ENDPOINTS ==============

@app.route('/api/books', methods=['GET'])
def get_books():
    """Get all books, optionally filtered by status"""
    try:
        book_manager, db = get_book_manager()
        status = request.args.get('status')  # 'read', 'to-read', 'currently-reading', or None for all
        
        all_books = book_manager.list_books()
        
        if status:
            books = [b for b in all_books if b['status'] == status]
        else:
            books = all_books
        
        stats = {
            'total': len(all_books),
            'read': len([b for b in all_books if b['status'] == 'read']),
            'to_read': len([b for b in all_books if b['status'] == 'to-read']),
            'currently_reading': len([b for b in all_books if b['status'] == 'currently-reading'])
        }
        
        db.close()
        
        return jsonify({
            'success': True,
            'books': books,
            'stats': stats,
            'count': len(books)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/books', methods=['POST'])
def add_book():
    """Add a new book"""
    try:
        data = request.json
        title = data.get('title', '').strip()
        author = data.get('author', '').strip()
        status = data.get('status', 'to-read').strip().lower()
        read_date = data.get('read_date', '').strip() or None
        
        if not title or not author:
            return jsonify({'success': False, 'error': 'Title and author are required'}), 400
        
        if status not in ['read', 'to-read', 'currently-reading']:
            status = 'to-read'
        
        book_manager, db = get_book_manager()
        book_manager.add_book(title, author, status, read_date)
        db.close()
        
        return jsonify({
            'success': True,
            'message': f'Added "{title}" by {author} [{status}]'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    """Delete a book"""
    try:
        book_manager, db = get_book_manager()
        book_manager.remove_book(book_id)
        db.close()
        
        return jsonify({'success': True, 'message': 'Book deleted'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/books/<int:book_id>/status', methods=['PUT'])
def update_book_status(book_id):
    """Update a book's status"""
    try:
        data = request.json
        new_status = data.get('status', '').strip().lower()
        read_date = data.get('read_date', '').strip() or None
        
        if new_status not in ['read', 'to-read', 'currently-reading']:
            return jsonify({'success': False, 'error': 'Invalid status'}), 400
        
        db = get_db()
        
        # If status is being set to 'read' and no date provided, use today's date
        if new_status == 'read' and not read_date:
            from datetime import datetime
            read_date = datetime.now().strftime('%m/%d/%Y')
        
        if read_date:
            query = "UPDATE books SET status = ?, read_date = ? WHERE id = ?"
            db.execute_query(query, (new_status, read_date, book_id))
        else:
            query = "UPDATE books SET status = ? WHERE id = ?"
            db.execute_query(query, (new_status, book_id))
        
        db.close()
        
        return jsonify({'success': True, 'message': f'Book status updated to {new_status}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/books/<int:book_id>/cover', methods=['PUT'])
def update_book_cover(book_id):
    """Update a book's cover URL"""
    try:
        data = request.json
        cover_url = data.get('cover_url', '').strip()
        
        if not cover_url:
            return jsonify({'success': False, 'error': 'Cover URL is required'}), 400
        
        db = get_db()
        query = "UPDATE books SET cover_url = ? WHERE id = ?"
        db.execute_query(query, (cover_url, book_id))
        db.close()
        
        return jsonify({'success': True, 'message': 'Cover updated'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/suggestions', methods=['GET'])
def get_suggestions():
    """Get book suggestions based on reading history"""
    try:
        num_suggestions = request.args.get('num', 5, type=int)
        
        suggester = get_llm_suggester()
        if not suggester or not suggester.client:
            return jsonify({
                'success': False,
                'error': 'LLM suggester not available. Please check your OpenAI API key.'
            }), 400
        
        book_manager, db = get_book_manager()
        all_books = book_manager.list_books()
        read_books = [b for b in all_books if b['status'] == 'read']
        
        if not read_books:
            db.close()
            return jsonify({
                'success': False,
                'error': 'You need to have read some books to get suggestions.'
            }), 400
        
        # Get rejected books to exclude from suggestions
        rejected_books = db.fetch_all("SELECT title, author FROM rejected_suggestions")
        
        suggestions = suggester.suggest_books(
            read_books, 
            all_books=all_books, 
            rejected_books=rejected_books,
            num_suggestions=num_suggestions
        )
        db.close()
        
        return jsonify({
            'success': True,
            'suggestions': suggestions,
            'count': len(suggestions)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/suggestions/add', methods=['POST'])
def add_suggestion_to_library():
    """Add a suggested book to the library as 'to-read'"""
    try:
        data = request.json
        title = data.get('title', '').strip()
        author = data.get('author', '').strip()
        
        if not title or not author:
            return jsonify({'success': False, 'error': 'Title and author are required'}), 400
        
        book_manager, db = get_book_manager()
        
        # Check if book already exists
        existing = db.fetch_all(
            "SELECT id FROM books WHERE LOWER(title) = LOWER(?) AND LOWER(author) = LOWER(?)",
            (title, author)
        )
        
        if existing:
            db.close()
            return jsonify({'success': False, 'error': 'Book already in your library'}), 400
        
        # Add with today's date as date_added
        from datetime import datetime
        date_added = datetime.now().strftime('%Y-%m-%d')
        
        db.execute_query(
            "INSERT INTO books (title, author, status, date_added) VALUES (?, ?, 'to-read', ?)",
            (title, author, date_added)
        )
        db.close()
        
        return jsonify({
            'success': True,
            'message': f'Added "{title}" to your reading list!'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/suggestions/reject', methods=['POST'])
def reject_suggestion():
    """Reject a suggestion so it won't be suggested again"""
    try:
        data = request.json
        title = data.get('title', '').strip()
        author = data.get('author', '').strip()
        reason = data.get('reason', '').strip()
        
        if not title or not author:
            return jsonify({'success': False, 'error': 'Title and author are required'}), 400
        
        db = get_db()
        
        # Check if already rejected
        existing = db.fetch_all(
            "SELECT id FROM rejected_suggestions WHERE LOWER(title) = LOWER(?) AND LOWER(author) = LOWER(?)",
            (title, author)
        )
        
        if existing:
            db.close()
            return jsonify({'success': True, 'message': 'Already rejected'})
        
        from datetime import datetime
        rejected_date = datetime.now().strftime('%Y-%m-%d')
        
        db.execute_query(
            "INSERT INTO rejected_suggestions (title, author, rejected_date, reason) VALUES (?, ?, ?, ?)",
            (title, author, rejected_date, reason)
        )
        db.close()
        
        return jsonify({
            'success': True,
            'message': f'"{title}" will not be suggested again'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/rejected', methods=['GET'])
def get_rejected():
    """Get list of rejected suggestions"""
    try:
        db = get_db()
        rejected = db.fetch_all("SELECT * FROM rejected_suggestions ORDER BY rejected_date DESC")
        db.close()
        return jsonify({'success': True, 'rejected': rejected, 'count': len(rejected)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/rejected/<int:rejected_id>', methods=['DELETE'])
def remove_rejected(rejected_id):
    """Remove a book from the rejected list"""
    try:
        db = get_db()
        db.execute_query("DELETE FROM rejected_suggestions WHERE id = ?", (rejected_id,))
        db.close()
        return jsonify({'success': True, 'message': 'Removed from rejected list'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get library statistics"""
    try:
        book_manager, db = get_book_manager()
        all_books = book_manager.list_books()
        db.close()
        
        stats = {
            'total_books': len(all_books),
            'read': len([b for b in all_books if b['status'] == 'read']),
            'to_read': len([b for b in all_books if b['status'] == 'to-read']),
            'currently_reading': len([b for b in all_books if b['status'] == 'currently-reading'])
        }
        
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    suggester = get_llm_suggester()
    return jsonify({
        'success': True,
        'message': 'API is running',
        'llm_available': suggester is not None and suggester.client is not None
    })

@app.route('/api/import', methods=['POST'])
def import_csv():
    """Import books from a CSV file (StoryGraph/Goodreads format)"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'error': 'File must be a CSV'}), 400
        
        # Read CSV content
        content = file.read().decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(content))
        
        book_manager, db = get_book_manager()
        
        # Get existing books to check for duplicates
        existing_books = book_manager.list_books()
        existing_titles = {(b['title'].lower(), b['author'].lower()) for b in existing_books}
        
        imported = 0
        skipped = 0
        
        for row in csv_reader:
            # Support both StoryGraph and Goodreads formats
            title = row.get('Title', row.get('title', '')).strip()
            author = row.get('Authors', row.get('Author', row.get('author', ''))).strip()
            
            # Handle status - StoryGraph uses "Read Status", Goodreads uses "Exclusive Shelf"
            status_raw = row.get('Read Status', row.get('Exclusive Shelf', 'to-read')).lower().strip()
            
            # Normalize status
            if status_raw in ['read', 'finished']:
                status = 'read'
            elif status_raw in ['currently-reading', 'currently reading', 'reading']:
                status = 'currently-reading'
            else:
                status = 'to-read'
            
            # Extract read date
            read_date = None
            if status == 'read':
                # StoryGraph format
                read_date = row.get('Last Date Read', '').strip()
                if not read_date:
                    dates_read = row.get('Dates Read', '').strip()
                    if dates_read and '-' in dates_read:
                        read_date = dates_read.split('-')[-1].strip()
                # Goodreads format
                if not read_date:
                    read_date = row.get('Date Read', '').strip()
            
            if title and author:
                # Check for duplicates
                if (title.lower(), author.lower()) in existing_titles:
                    skipped += 1
                    continue
                
                book_manager.add_book(title, author, status, read_date)
                existing_titles.add((title.lower(), author.lower()))
                imported += 1
        
        # Get updated count
        all_books = book_manager.list_books()
        db.close()
        
        return jsonify({
            'success': True,
            'imported': imported,
            'skipped': skipped,
            'total': len(all_books)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============== ERROR HANDLERS ==============

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
