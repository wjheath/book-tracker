# 📚 Book Tracker & Suggester

A Python app that tracks your reading list and uses AI to suggest personalized book recommendations based on your reading history.

## ⚡ Quick Start

### Windows
```
Double-click: start.bat
```

### Mac/Linux/Manual
```bash
python run_ui.py
```

Then open: **http://127.0.0.1:5000**

## ✨ Features

- 📖 **Book Library** - Manage your reading list with status tracking
- 🤖 **AI Suggestions** - Get personalized recommendations powered by OpenAI
- 🔍 **Filter by Status** - Read, To-Read, Currently Reading
- 📊 **Statistics** - Track your reading habits
- 📱 **Web UI** - Clean, responsive interface

## 📁 Project Structure

```
book-tracker-app/
├── src/
│   ├── app.py              # Flask API backend
│   ├── index.html          # Web UI
│   ├── llm_suggester.py    # AI suggestions
│   ├── database.py         # SQLite operations
│   ├── book_manager.py     # Book CRUD operations
│   └── config.py           # Configuration
├── data/
│   └── books.db            # SQLite database
├── prompts/
│   └── book_suggestion.txt # Customizable AI prompt
├── start.bat               # Windows launcher
├── run_ui.py               # Python launcher
├── .env                    # Configuration (API key)
└── requirements.txt        # Python packages
```

## 🚀 Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Key (for AI Suggestions)
Create a `.env` file (or edit existing):
```
OPENAI_API_KEY=sk-your-key-here
```
Get a key from: https://platform.openai.com/api-keys

### 3. Run the App
- **Windows**: Double-click `start.bat`
- **Other OS**: Run `python run_ui.py`

## 🎨 Using the App

### Library Management
- View all your books with status indicators
- Add new books with title, author, and status
- Change status with one click (Read/To-Read/Currently Reading)
- Delete books you no longer want to track

### AI Suggestions
- Click "Get Suggestions" in the UI
- Choose how many recommendations (3, 5, or 10)
- Receive personalized suggestions with reasons based on your reading history

## 🔧 Configuration

### Environment Variables (.env)
```
OPENAI_API_KEY=sk-...          # Required for AI suggestions
OPENAI_MODEL=gpt-4o-mini       # Model to use (optional)
```

### Custom Prompts
Edit `prompts/book_suggestion.txt` to customize how AI generates recommendations.

## 📚 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/books` | Get all books |
| GET | `/api/books?status=read` | Filter by status |
| POST | `/api/books` | Add a book |
| DELETE | `/api/books/<id>` | Delete a book |
| PUT | `/api/books/<id>/status` | Update book status |
| GET | `/api/suggestions?num=5` | Get AI suggestions |
| GET | `/api/stats` | Get library statistics |
| GET | `/api/health` | Health check |

## 🆘 Troubleshooting

**Python not found?**
- Install Python 3.8+ from https://www.python.org/
- Ensure "Add Python to PATH" is checked during installation
- Restart your terminal/computer after installation

**AI suggestions not working?**
- Verify your API key is correct in `.env`
- Check you have API credits at https://platform.openai.com/usage
- Ensure you have read books in your library (suggestions need history)

**App won't start?**
- Run `pip install -r requirements.txt` to install dependencies
- Try running directly: `python src/app.py`

## 📄 License

MIT License

