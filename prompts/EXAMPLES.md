# CUSTOM PROMPT EXAMPLES
# =====================
#
# You can customize the book suggestion prompt by editing this file
# or by creating a new file in the prompts/ directory and setting:
#   CUSTOM_PROMPT_FILE=/path/to/your/prompt.txt in .env
#
# Available variables:
#   {books_list}      - List of books the user has read
#   {num_suggestions} - Number of suggestions to return
#
# ============================================================================

## EXAMPLE 1: Simple and Direct
# Based on the following books the user has read:
# 
# {books_list}
# 
# Please suggest {num_suggestions} new books they might enjoy. Include title, author, and why.


## EXAMPLE 2: Focus on Hidden Gems
# The user has read these books:
# 
# {books_list}
# 
# Suggest {num_suggestions} lesser-known but highly acclaimed books they might not have discovered yet.
# For each, provide: title, author, and one reason why it matches their taste.


## EXAMPLE 3: Adventure & Exploration Focused
# Books this reader has enjoyed:
# 
# {books_list}
# 
# Based on their reading history, recommend {num_suggestions} books with great world-building,
# compelling characters, and immersive storytelling. Format: numbered list with title, author, and reason.


## EXAMPLE 4: Mood-Based Suggestions
# The user loves these books:
# 
# {books_list}
# 
# Suggest {num_suggestions} books that match their reading mood - looking for books that are:
# - Engaging and hard to put down
# - Well-written with strong character development
# - Similar in tone and scope to what they've enjoyed
#
# For each suggestion: title, author, and why it's a good fit.


## EXAMPLE 5: Academic/Literary Focus
# This reader has explored:
# 
# {books_list}
# 
# Please recommend {num_suggestions} intellectually stimulating books with literary merit.
# Include: title, author, and a brief explanation of why this book would resonate with them.


## EXAMPLE 6: Diverse & Different Recommendations
# The user has read:
# 
# {books_list}
# 
# Suggest {num_suggestions} books that are different from what they've read, but still aligned with
# their demonstrated interests. Push them gently outside their comfort zone while respecting their tastes.
# Format: numbered list with title, author, and brief reason.


## HOW TO USE:
# 1. Pick an example above that resonates with you
# 2. Copy it to prompts/book_suggestion.txt
# 3. Restart the app or re-import the module
# 4. Run a suggestion query and see the results!
