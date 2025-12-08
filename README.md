# 📚 Book Tracker & Suggester

A Python app that tracks your reading list and uses AI to suggest new books based on your reading history.

## ⚡ Quick Start

### Windows
```
Double-click: start_ui_simple.bat
```

### Mac/Linux
```bash
python run_ui.py
```

### Manual
```bash
python src/app.py
# Then visit: http://127.0.0.1:5000
```

## ✨ Features

- 📖 **Book Library** - Manage your reading list (239 books included)
- 🔍 **Filter by Status** - Read, To-Read, Currently Reading
- 🤖 **AI Suggestions** - Get personalized book recommendations
- 📱 **Web UI** - Beautiful, responsive interface
- 🎯 **Real-time Updates** - See changes instantly
- 📊 **Statistics** - Track your reading habits

## 📁 Project Structure

```
book-tracker-app/
├── src/
│   ├── app.py              # Flask API backend
│   ├── index.html          # Web UI
│   ├── llm_suggester.py    # AI suggestions
│   ├── database.py         # SQLite operations
│   └── ...
├── data/
│   └── books.db            # SQLite database (239 books)
├── prompts/
│   └── book_suggestion.txt # Custom LLM prompt
├── start_ui_simple.bat     # Windows launcher
├── run_ui.py               # Python launcher
├── .env                    # Configuration (API keys)
├── requirements.txt        # Python packages
└── README.md              # This file
```

## 🚀 Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Key (Optional, for AI Suggestions)
1. Edit `.env` file
2. Add your OpenAI API key:
```
OPENAI_API_KEY=sk-your-key-here
```
Get it from: https://platform.openai.com/account/api-keys

### 3. Start the App
- **Windows**: Double-click `start_ui_simple.bat`
- **Others**: Run `python run_ui.py`
- **Manual**: Run `python src/app.py`

### 4. Open Browser
Visit: `http://127.0.0.1:5000`

## 🎨 Web UI

### Dashboard
- View statistics (total, read, to-read, currently reading)
- Beautiful gradient design

### Library Management
- View all 239 books
- Add new books
- Change status with one click
- Delete books
- Filter by status

### AI Suggestions
- Get personalized recommendations
- Choose 3, 5, or 10 suggestions
- See why each book is recommended
- Avoids books already in library

## 🔧 Configuration

### .env File
```
OPENAI_API_KEY=sk-your-key-here     # For AI suggestions
OPENAI_MODEL=gpt-4o-mini            # AI model
OPENAI_REASONING=medium             # Reasoning level
```

### Custom Prompts
Edit `prompts/book_suggestion.txt` to customize AI suggestions.

## 📚 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/books` | Get all books |
| POST | `/api/books` | Add book |
| DELETE | `/api/books/<id>` | Delete book |
| PUT | `/api/books/<id>/status` | Update status |
| GET | `/api/suggestions?num=5` | Get AI suggestions |
| GET | `/api/stats` | Get statistics |

## 🆘 Troubleshooting

**Python not found?**
- Try: `start_ui_simple.bat`
- Then try: `python run_ui.py`
- Read: `TROUBLESHOOTING.md`

**Suggestions not working?**
- Check `.env` has valid API key
- Wait 10-30 seconds (AI takes time)
- Read: `TROUBLESHOOTING.md`

**Books not loading?**
- Check `data/books.db` exists
- Run: `python src/inspect_db.py`


## 📖 Documentation

- **README.md** - Main overview (this file)
- **QUICK_START.md** - Getting started steps
- **TROUBLESHOOTING.md** - All help in one place
- **LLM_IMPROVEMENTS.md** - AI suggestion improvements
- **UI_README.md** - API reference

## 💡 Tips

- **Mobile Access**: Visit `http://<your-ip>:5000` from phone on same network
- **Custom Prompts**: Edit `prompts/book_suggestion.txt`
- **Import CSV**: Use `python src/import_books.py`
- **Check DB**: Run `python src/inspect_db.py`

