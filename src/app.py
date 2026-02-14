import os
import sys
import csv
import io
import json
import traceback
from datetime import datetime
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from database import Database
from book_manager import BookManager
from llm_suggester import LLM_Suggester
from chat_engine import BookChatEngine
from reader_profile import ReaderProfile

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

# Singleton chat engine (reused across requests)
_chat_engine = None
def get_chat_engine():
    global _chat_engine
    if _chat_engine is None:
        try:
            _chat_engine = BookChatEngine()
        except Exception as e:
            print(f"Warning: Could not initialize chat engine: {e}")
            return None
    return _chat_engine

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

@app.route('/api/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    """Update a book's full record (admin mode)"""
    try:
        data = request.json
        db = get_db()
        
        # Check book exists
        existing = db.fetch_all("SELECT * FROM books WHERE id = ?", (book_id,))
        if not existing:
            db.close()
            return jsonify({'success': False, 'error': 'Book not found'}), 404
        
        book = existing[0]
        
        # Update fields that were provided
        title = data.get('title', book['title']).strip() if data.get('title') else book['title']
        author = data.get('author', book['author']).strip() if data.get('author') else book['author']
        status = data.get('status', book['status']).strip().lower() if data.get('status') else book['status']
        read_date = data.get('read_date', book.get('read_date'))
        genre = data.get('genre', book.get('genre'))
        cover_url = data.get('cover_url', book.get('cover_url'))
        date_added = data.get('date_added', book.get('date_added'))
        
        if not title or not author:
            db.close()
            return jsonify({'success': False, 'error': 'Title and author are required'}), 400
        
        if status not in ['read', 'to-read', 'currently-reading']:
            db.close()
            return jsonify({'success': False, 'error': 'Invalid status'}), 400
        
        query = """UPDATE books 
                   SET title = ?, author = ?, status = ?, read_date = ?, 
                       genre = ?, cover_url = ?, date_added = ?
                   WHERE id = ?"""
        db.execute_query(query, (title, author, status, read_date, genre, cover_url, date_added, book_id))
        
        # Fetch updated record
        updated = db.fetch_all("SELECT * FROM books WHERE id = ?", (book_id,))
        db.close()
        
        return jsonify({'success': True, 'book': updated[0] if updated else None, 'message': 'Book updated'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/books/bulk-delete', methods=['POST'])
def bulk_delete_books():
    """Delete multiple books at once (admin mode)"""
    try:
        data = request.json
        book_ids = data.get('ids', [])
        
        if not book_ids:
            return jsonify({'success': False, 'error': 'No book IDs provided'}), 400
        
        db = get_db()
        placeholders = ','.join('?' * len(book_ids))
        query = f"DELETE FROM books WHERE id IN ({placeholders})"
        db.execute_query(query, tuple(book_ids))
        db.close()
        
        return jsonify({'success': True, 'message': f'Deleted {len(book_ids)} books', 'deleted': len(book_ids)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/books/export', methods=['GET'])
def export_books():
    """Export all books as CSV"""
    try:
        book_manager, db = get_book_manager()
        all_books = book_manager.list_books()
        db.close()
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=['id', 'title', 'author', 'status', 'read_date', 'genre', 'date_added'])
        writer.writeheader()
        for book in all_books:
            writer.writerow({
                'id': book.get('id', ''),
                'title': book.get('title', ''),
                'author': book.get('author', ''),
                'status': book.get('status', ''),
                'read_date': book.get('read_date', ''),
                'genre': book.get('genre', ''),
                'date_added': book.get('date_added', '')
            })
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=books_export.csv'}
        )
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

# ============== CHAT API ENDPOINTS ==============

@app.route('/api/chat', methods=['POST'])
def chat_message():
    """Send a message to the conversational book recommendation engine"""
    try:
        data = request.json
        message = data.get('message', '').strip()
        conversation_id = data.get('conversation_id')
        
        if not message:
            return jsonify({'success': False, 'error': 'Message is required'}), 400
        
        engine = get_chat_engine()
        if not engine or not engine.graph:
            return jsonify({
                'success': False,
                'error': 'Chat engine not available. Please check your OpenAI API key.'
            }), 400
        
        # Load conversation state from DB if continuing
        db = get_db()
        messages = []
        gathered_preferences = {}
        
        if conversation_id:
            convos = db.fetch_all(
                "SELECT messages, gathered_preferences FROM conversations WHERE id = ?",
                (conversation_id,)
            )
            if convos:
                try:
                    messages = json.loads(convos[0].get('messages', '[]'))
                    gathered_preferences = json.loads(convos[0].get('gathered_preferences', '{}'))
                except (json.JSONDecodeError, TypeError):
                    messages = []
                    gathered_preferences = {}
        
        # Get book data for context
        book_manager, _ = get_book_manager()
        all_books = book_manager.list_books()
        read_books = [b for b in all_books if b.get('status') == 'read']
        rejected_books = db.fetch_all("SELECT title, author FROM rejected_suggestions")
        
        # Process message through LangGraph engine
        result = engine.chat_sync(
            message=message,
            conversation_id=conversation_id,
            messages=messages,
            read_books=read_books,
            all_books=all_books,
            rejected_books=rejected_books,
            gathered_preferences=gathered_preferences,
        )
        
        # Save conversation state to DB
        conv_id = result.get('conversation_id', conversation_id)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Generate a title from the first user message
        conv_title = message[:80] + ('...' if len(message) > 80 else '')
        
        if conversation_id:
            db.execute_query(
                "UPDATE conversations SET updated_at = ?, messages = ?, gathered_preferences = ? WHERE id = ?",
                (now, json.dumps(result.get('messages', [])), json.dumps(result.get('gathered_preferences', {})), conv_id)
            )
        else:
            db.execute_query(
                "INSERT INTO conversations (id, created_at, updated_at, title, messages, gathered_preferences) VALUES (?, ?, ?, ?, ?, ?)",
                (conv_id, now, now, conv_title, json.dumps(result.get('messages', [])), json.dumps(result.get('gathered_preferences', {})))
            )
        
        db.close()
        
        return jsonify({
            'success': True,
            'response': result.get('response', ''),
            'suggestions': result.get('suggestions', []),
            'conversation_id': conv_id,
            'intent': result.get('intent', ''),
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/chat/conversations', methods=['GET'])
def list_conversations():
    """List all conversations"""
    try:
        db = get_db()
        convos = db.fetch_all(
            "SELECT id, created_at, updated_at, title FROM conversations WHERE is_active = 1 ORDER BY updated_at DESC"
        )
        db.close()
        return jsonify({'success': True, 'conversations': convos})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/chat/conversations/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """Get a specific conversation with full message history"""
    try:
        db = get_db()
        convos = db.fetch_all(
            "SELECT * FROM conversations WHERE id = ?",
            (conversation_id,)
        )
        db.close()
        
        if not convos:
            return jsonify({'success': False, 'error': 'Conversation not found'}), 404
        
        convo = convos[0]
        try:
            convo['messages'] = json.loads(convo.get('messages', '[]'))
            convo['gathered_preferences'] = json.loads(convo.get('gathered_preferences', '{}'))
        except (json.JSONDecodeError, TypeError):
            convo['messages'] = []
            convo['gathered_preferences'] = {}
        
        return jsonify({'success': True, 'conversation': convo})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/chat/conversations/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """Delete a conversation"""
    try:
        db = get_db()
        db.execute_query("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        db.close()
        return jsonify({'success': True, 'message': 'Conversation deleted'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/profile', methods=['GET'])
def get_reader_profile():
    """Get the reader's DNA profile analysis"""
    try:
        book_manager, db = get_book_manager()
        all_books = book_manager.list_books()
        read_books = [b for b in all_books if b.get('status') == 'read']
        db.close()
        
        if not read_books:
            return jsonify({
                'success': False,
                'error': 'Need read books to build a profile'
            }), 400
        
        profile = ReaderProfile(all_books, all_books)
        profile_data = profile.build()
        profile_text = profile.get_prompt_context()
        
        return jsonify({
            'success': True,
            'profile': profile_data,
            'profile_text': profile_text,
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
