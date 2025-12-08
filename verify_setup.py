#!/usr/bin/env python
"""
Book Tracker - Setup Verification Script
Checks that everything is installed and configured correctly
"""

import os
import sys
from pathlib import Path

def print_header():
    print("\n" + "=" * 70)
    print("  📚 BOOK TRACKER - SETUP VERIFICATION")
    print("=" * 70 + "\n")

def check_item(item_name, condition, details=""):
    status = "✅ PASS" if condition else "❌ FAIL"
    print(f"{status} | {item_name}")
    if details:
        print(f"       {details}")

def main():
    print_header()
    
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print("Checking project setup...\n")
    
    # 1. Check Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    check_item(
        "Python Version",
        sys.version_info >= (3, 8),
        f"Found Python {python_version}"
    )
    
    # 2. Check required directories
    print()
    print("Directory Structure:")
    dirs_ok = True
    for dir_name in ['src', 'data', 'prompts']:
        exists = (project_root / dir_name).exists()
        check_item(f"  {dir_name}/ directory", exists)
        dirs_ok = dirs_ok and exists
    
    # 3. Check required files
    print()
    print("Required Files:")
    files_ok = True
    for file_name in ['src/app.py', 'src/index.html', 'data/books.db', '.env.example']:
        exists = (project_root / file_name).exists()
        check_item(f"  {file_name}", exists)
        files_ok = files_ok and exists
    
    # 4. Check Python packages
    print()
    print("Python Packages:")
    packages = {
        'flask': 'Flask (web framework)',
        'flask_cors': 'Flask-CORS (cross-origin support)',
        'openai': 'OpenAI (LLM integration)',
        'dotenv': 'python-dotenv (environment variables)',
    }
    
    packages_ok = True
    for package, description in packages.items():
        try:
            __import__(package)
            check_item(f"  {description}", True)
        except ImportError:
            check_item(f"  {description}", False, "Install with: pip install -r requirements.txt")
            packages_ok = False
    
    # 5. Check configuration
    print()
    print("Configuration:")
    env_exists = (project_root / '.env').exists()
    check_item(
        "  .env file",
        env_exists,
        "Contains OPENAI_API_KEY" if env_exists else "See .env.example"
    )
    
    # 6. Check database
    print()
    print("Database:")
    db_exists = (project_root / 'data' / 'books.db').exists()
    check_item(
        "  books.db file",
        db_exists,
        "SQLite database" if db_exists else "Import books first: python src/import_books.py"
    )
    
    # 7. Check launchers
    print()
    print("Launchers:")
    check_item(
        "  run_ui.py (Python launcher)",
        (project_root / 'run_ui.py').exists()
    )
    check_item(
        "  start_ui.bat (Windows launcher)",
        (project_root / 'start_ui.bat').exists(),
        "Windows only - double-click to start"
    )
    
    # Summary
    print()
    print("=" * 70)
    
    all_ok = dirs_ok and files_ok and packages_ok
    
    if all_ok:
        print("✅ ALL CHECKS PASSED - Ready to use!")
        print()
        print("Next steps:")
        print("  1. Windows: Double-click start_ui.bat")
        print("  2. Mac/Linux: Run 'python run_ui.py'")
        print("  3. Manual: Run 'python src/app.py' then visit http://127.0.0.1:5000")
        print()
    else:
        print("❌ SOME CHECKS FAILED - Please fix issues above")
        print()
        print("Common fixes:")
        print("  • Install packages: pip install -r requirements.txt")
        print("  • Create .env file: copy .env.example to .env")
        print("  • Import books: python src/import_books.py")
        print()
    
    print("=" * 70 + "\n")
    
    return 0 if all_ok else 1

if __name__ == '__main__':
    sys.exit(main())
