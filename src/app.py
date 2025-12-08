import os
import sys
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
            return jsonify({
                'success': False,
                'error': 'You need to have read some books to get suggestions.'
            }), 400
        
        suggestions = suggester.suggest_books(read_books, all_books=all_books, num_suggestions=num_suggestions)
        db.close()
        
        return jsonify({
            'success': True,
            'suggestions': suggestions,
            'count': len(suggestions)
        })
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

# ============== ERROR HANDLERS ==============

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
