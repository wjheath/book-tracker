/* ============================================================
   Book Tracker & Suggester — Application JavaScript
   ============================================================ */

// ============== CONFIGURATION ==============
const API_URL = '/api';
let currentFilter = null;
let allBooks = [];
let filteredBooks = [];
let searchQuery = '';
let currentSort = 'id-desc';
let visibleCount = 50;
const BOOKS_PER_BATCH = 50;
let scrollObserver = null;

// Admin state
let adminBooks = [];
let adminSearchQuery = '';
let adminSortCol = 'id';
let adminSortDir = 'asc';
let adminSelected = new Set();
let adminEditingCell = null;

// ============== SVG ICON HELPERS ==============
const Icons = {
    check: '<svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>',
    x: '<svg viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
    info: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
    trash: '<svg viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>',
    book: '<svg viewBox="0 0 24 24"><path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/></svg>',
    plus: '<svg viewBox="0 0 24 24"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>',
    upload: '<svg viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>',
    download: '<svg viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>',
    refresh: '<svg viewBox="0 0 24 24"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/></svg>',
};

// ============== TOAST NOTIFICATIONS ==============
function toast(message, type = 'info', duration = 3500) {
    const container = document.getElementById('toastContainer');
    const iconMap = {
        success: Icons.check,
        error: Icons.x,
        info: Icons.info,
    };
    const el = document.createElement('div');
    el.className = `toast ${type}`;
    el.innerHTML = `<span class="toast-icon">${iconMap[type] || iconMap.info}</span><span class="toast-text">${escapeHtml(message)}</span>`;
    container.appendChild(el);
    setTimeout(() => {
        el.classList.add('fade-out');
        setTimeout(() => el.remove(), 300);
    }, duration);
}

// ============== TAB NAVIGATION ==============
function switchTab(tabName, btn) {
    document.querySelectorAll('.tab-page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
    document.getElementById('tab-' + tabName).classList.add('active');
    if (btn) btn.classList.add('active');

    if (tabName === 'admin') adminRefresh();
    if (tabName === 'library') loadBooks();
    if (tabName === 'chat') chatLoadConversations();
    if (tabName === 'profile') loadProfile();
    if (tabName === 'suggestions') loadRejected();
}

// ============== UTILITY ==============
function escapeHtml(text) {
    if (text == null) return '';
    const str = String(text);
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return str.replace(/[&<>"']/g, m => map[m]);
}

function showMessage(elementId, message, type) {
    const element = document.getElementById(elementId);
    element.innerHTML = `<div class="alert alert-${type}" style="margin-top: 15px;">${message}</div>`;
    setTimeout(() => { element.innerHTML = ''; }, 5000);
}

function formatStatus(status) {
    const map = {
        'read': 'Read',
        'to-read': 'To Read',
        'currently-reading': 'Reading',
    };
    return map[status] || status;
}

function formatStatusDropdown(status) {
    const map = {
        'to-read': 'To Read',
        'currently-reading': 'Reading',
        'read': 'Read',
    };
    return map[status] || status;
}

// ============== BOOK STATUS DATE TOGGLE ==============
document.getElementById('bookStatus').addEventListener('change', function () {
    document.getElementById('readDateGroup').style.display =
        this.value === 'read' ? 'block' : 'none';
});

// ============== CSV IMPORT ==============
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');

dropZone.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
});
dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
});
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    if (e.dataTransfer.files.length > 0) handleFileUpload(e.dataTransfer.files[0]);
});
fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) handleFileUpload(e.target.files[0]);
});

async function handleFileUpload(file) {
    if (!file.name.endsWith('.csv')) {
        toast('Please upload a CSV file', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    const dropZoneDefault = `
        <div class="drop-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg></div>
        <div class="drop-zone-text">Drop your CSV file here</div>
        <div class="drop-zone-hint">or click to browse</div>`;

    dropZone.innerHTML = `
        <div class="spinner"></div>
        <div class="drop-zone-text" style="margin-top: 15px;">Importing ${escapeHtml(file.name)}...</div>`;

    try {
        const response = await fetch(`${API_URL}/import`, { method: 'POST', body: formData });
        const data = await response.json();
        dropZone.innerHTML = dropZoneDefault;

        if (data.success) {
            toast(`Imported ${data.imported} books`, 'success');
            document.getElementById('importResults').innerHTML = `<div class="import-results">
                <h4>Import Summary</h4>
                <ul>
                    <li>Imported: ${data.imported} books</li>
                    <li>Skipped (duplicates): ${data.skipped || 0}</li>
                    <li>Total in library: ${data.total || 'N/A'}</li>
                </ul>
            </div>`;
            loadBooks();
            loadStats();
        } else {
            toast(data.error || 'Error importing file', 'error');
        }
    } catch (error) {
        dropZone.innerHTML = dropZoneDefault;
        toast('Error: ' + error.message, 'error');
    }
    fileInput.value = '';
}

// ============== SEARCH & FILTER & SORT ==============
function searchBooks() {
    searchQuery = document.getElementById('searchInput').value.toLowerCase().trim();
    renderFilteredBooks();
}

function renderFilteredBooks() {
    let filtered = allBooks;
    if (currentFilter) {
        filtered = filtered.filter(b => b.status === currentFilter);
    }
    if (searchQuery) {
        filtered = filtered.filter(b =>
            (b.title || '').toLowerCase().includes(searchQuery) ||
            (b.author || '').toLowerCase().includes(searchQuery)
        );
    }
    filtered = applySorting(filtered);
    filteredBooks = filtered;
    visibleCount = BOOKS_PER_BATCH;
    renderBooks();
}

function parseDateVal(str) {
    if (!str) return null;
    const mdyMatch = str.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
    if (mdyMatch) return parseInt(mdyMatch[3] + mdyMatch[1].padStart(2, '0') + mdyMatch[2].padStart(2, '0'), 10);
    const isoMatch = str.match(/^(\d{4})-(\d{2})-(\d{2})$/);
    if (isoMatch) return parseInt(isoMatch[1] + isoMatch[2] + isoMatch[3], 10);
    return null;
}

function applySorting(books) {
    const [field, dir] = currentSort.split('-').length >= 2
        ? [currentSort.slice(0, currentSort.lastIndexOf('-')), currentSort.slice(currentSort.lastIndexOf('-') + 1)]
        : [currentSort, 'asc'];
    const mult = dir === 'desc' ? -1 : 1;
    const dateFields = new Set(['read_date', 'date', 'date_added']);
    return [...books].sort((a, b) => {
        if (field === 'id') return (a.id - b.id) * mult;
        if (dateFields.has(field)) {
            const va = parseDateVal(a[field]);
            const vb = parseDateVal(b[field]);
            if (va === null && vb === null) return 0;
            if (va === null) return 1;
            if (vb === null) return -1;
            return (va - vb) * mult;
        }
        let va = (a[field] || '').toLowerCase();
        let vb = (b[field] || '').toLowerCase();
        if (va < vb) return -1 * mult;
        if (va > vb) return 1 * mult;
        return 0;
    });
}

function sortBooks(value) {
    currentSort = value;
    renderFilteredBooks();
}

// ============== INIT ==============
document.addEventListener('DOMContentLoaded', () => {
    loadBooks();
    loadStats();
});

// ============== ADD BOOK ==============
document.getElementById('addBookForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const title = document.getElementById('bookTitle').value.trim();
    const author = document.getElementById('bookAuthor').value.trim();
    const status = document.getElementById('bookStatus').value;
    const readDate = document.getElementById('bookReadDate').value || null;

    try {
        const response = await fetch(`${API_URL}/books`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, author, status, read_date: readDate }),
        });
        const data = await response.json();

        if (data.success) {
            toast(`Added "${title}" by ${author}`, 'success');
            document.getElementById('addBookForm').reset();
            document.getElementById('readDateGroup').style.display = 'none';
            loadBooks();
            loadStats();
        } else {
            toast(data.error || 'Error adding book', 'error');
        }
    } catch (error) {
        toast('Error: ' + error.message, 'error');
    }
});

// ============== LOAD BOOKS ==============
async function loadBooks() {
    try {
        const response = await fetch(`${API_URL}/books`);
        const data = await response.json();
        if (data.success) {
            allBooks = data.books;
            renderFilteredBooks();
        }
    } catch (error) {
        document.getElementById('bookListContainer').innerHTML =
            `<div class="alert alert-error">Error loading books: ${error.message}</div>`;
    }
}

// ============== RENDER BOOKS (infinite scroll) ==============
function renderBooks() {
    const books = filteredBooks;
    const container = document.getElementById('bookListContainer');
    const total = books.length;

    // Disconnect any previous scroll observer
    if (scrollObserver) { scrollObserver.disconnect(); scrollObserver = null; }

    if (total === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M4 19.5A2.5 2.5 0 016.5 17H20"/>
                        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/>
                    </svg>
                </div>
                <h3>No books found</h3>
                <p>Start by adding a book to your library</p>
            </div>`;
        return;
    }

    const shown = Math.min(visibleCount, total);
    const visibleBooks = books.slice(0, shown);
    const hasMore = shown < total;

    container.innerHTML = `
        <div class="library-counter">
            Showing ${shown} of ${total} book${total !== 1 ? 's' : ''}${hasMore ? ' &mdash; scroll down for more' : ''}
        </div>
        <div class="book-list">
            ${visibleBooks.map(book => {
                const initials = getBookInitials(book.title);
                return `
                <div class="book-item" id="book-item-${book.id}">
                    <div class="book-content">
                        <div class="cover-wrapper" onclick="openCoverPicker(${book.id})" title="Click to change cover">
                            ${book.cover_url
                                ? `<img src="${escapeHtml(book.cover_url)}" class="book-cover" alt="Cover" onerror="this.outerHTML='<div class=book-cover-placeholder>${initials}</div>'">`
                                : `<div class="book-cover-placeholder" data-book-id="${book.id}" data-title="${escapeHtml(book.title)}" data-author="${escapeHtml(book.author)}">${initials}</div>`
                            }
                            <div class="cover-edit-badge"><svg viewBox="0 0 24 24" width="10" height="10" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3a2.828 2.828 0 114 4L7.5 20.5 2 22l1.5-5.5L17 3z"/></svg></div>
                        </div>
                        <div class="book-info">
                            <div class="book-title">${escapeHtml(book.title)}</div>
                            <div class="book-author">by ${escapeHtml(book.author)}</div>
                            ${book.read_date ? `<div class="book-date">Read: ${escapeHtml(book.read_date)}</div>` : ''}
                            ${book.genre ? `<div class="book-genre">${escapeHtml(book.genre)}</div>` : ''}
                        </div>
                    </div>
                    <div class="book-actions">
                        <select class="status-dropdown" onchange="updateStatus(${book.id}, this.value)">
                            <option value="to-read" ${book.status === 'to-read' ? 'selected' : ''}>To Read</option>
                            <option value="currently-reading" ${book.status === 'currently-reading' ? 'selected' : ''}>Reading</option>
                            <option value="read" ${book.status === 'read' ? 'selected' : ''}>Read</option>
                        </select>
                        <button class="delete-btn" onclick="deleteBook(${book.id})" title="Delete">
                            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
                            </svg>
                        </button>
                    </div>
                </div>`;
            }).join('')}
        </div>
        ${hasMore ? '<div class="scroll-sentinel" id="scrollSentinel"><div class="spinner" style="width:24px;height:24px;border-width:2px;"></div><span>Loading more books...</span></div>' : ''}
        ${!hasMore && total > BOOKS_PER_BATCH ? '<div class="library-end-marker">You\'ve reached the end of your library</div>' : ''}`;

    // Set up IntersectionObserver for infinite scroll
    if (hasMore) {
        const sentinel = document.getElementById('scrollSentinel');
        if (sentinel) {
            scrollObserver = new IntersectionObserver(entries => {
                if (entries[0].isIntersecting) {
                    visibleCount += BOOKS_PER_BATCH;
                    renderBooks();
                }
            }, { rootMargin: '200px' });
            scrollObserver.observe(sentinel);
        }
    }

    fetchMissingCovers();
}

function getBookInitials(title) {
    if (!title) return 'B';
    const words = title.replace(/[^a-zA-Z\s]/g, '').split(/\s+/).filter(Boolean);
    if (words.length === 0) return 'B';
    if (words.length === 1) return words[0].charAt(0).toUpperCase();
    return (words[0].charAt(0) + words[1].charAt(0)).toUpperCase();
}

// ============== FILTER ==============
function filterBooks(status, btnElement) {
    currentFilter = status;
    document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
    if (btnElement) btnElement.classList.add('active');
    renderFilteredBooks();
}

// ============== DELETE BOOK ==============
async function deleteBook(bookId) {
    const book = allBooks.find(b => b.id === bookId);
    const title = book ? book.title : 'this book';
    if (!confirm(`Delete "${title}"?`)) return;

    const el = document.getElementById('book-item-' + bookId);
    if (el) {
        el.style.transition = 'opacity 0.3s, transform 0.3s';
        el.style.opacity = '0';
        el.style.transform = 'translateX(50px)';
    }

    try {
        const response = await fetch(`${API_URL}/books/${bookId}`, { method: 'DELETE' });
        const data = await response.json();

        if (data.success) {
            allBooks = allBooks.filter(b => b.id !== bookId);
            toast('Book deleted', 'success');
            renderFilteredBooks();
            loadStats();
        } else {
            if (el) { el.style.opacity = '1'; el.style.transform = 'none'; }
            toast(data.error || 'Failed to delete book', 'error');
        }
    } catch (error) {
        if (el) { el.style.opacity = '1'; el.style.transform = 'none'; }
        toast('Error deleting book: ' + error.message, 'error');
    }
}

// ============== UPDATE STATUS ==============
async function updateStatus(bookId, newStatus) {
    try {
        const body = { status: newStatus };
        if (newStatus === 'read') {
            const today = new Date();
            body.read_date = `${String(today.getMonth() + 1).padStart(2, '0')}/${String(today.getDate()).padStart(2, '0')}/${today.getFullYear()}`;
        }

        const response = await fetch(`${API_URL}/books/${bookId}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        const data = await response.json();

        if (data.success) {
            const book = allBooks.find(b => b.id === bookId);
            if (book) {
                book.status = newStatus;
                if (newStatus === 'read' && body.read_date) book.read_date = body.read_date;
            }
            toast(`Status updated to ${formatStatus(newStatus)}`, 'success');
            loadStats();
            renderFilteredBooks();
        } else {
            toast('Failed to update status', 'error');
        }
    } catch (error) {
        toast('Error updating status: ' + error.message, 'error');
    }
}

// ============== BOOK COVERS ==============
const OL_SUBJECT_MAP = [
    ['urban fantasy', 'urban fantasy'],
    ['fantasy', 'fantasy'],
    ['magic', 'fantasy'],
    ['wizard', 'fantasy'],
    ['dragon', 'fantasy'],
    ['fairy', 'fantasy'],
    ['mytholog', 'fantasy'],
    ['science fiction', 'science fiction'],
    ['space opera', 'science fiction'],
    ['cyberpunk', 'science fiction'],
    ['dystopi', 'dystopian'],
    ['mystery', 'mystery'],
    ['detective', 'mystery'],
    ['crime fiction', 'mystery'],
    ['thriller', 'thriller'],
    ['suspense', 'thriller'],
    ['horror', 'horror'],
    ['ghost stori', 'horror'],
    ['occult', 'horror'],
    ['romance', 'romance'],
    ['historical fiction', 'historical fiction'],
    ['historical novel', 'historical fiction'],
    ['literary fiction', 'literary fiction'],
    ['psychological fiction', 'literary fiction'],
    ['magical realism', 'magical realism'],
    ['young adult', 'young adult'],
    ['juvenile fiction', 'young adult'],
    ['children', 'children'],
    ['graphic novel', 'graphic novel'],
    ['comic', 'graphic novel'],
    ['manga', 'graphic novel'],
    ['biography', 'memoir'],
    ['autobiography', 'memoir'],
    ['memoir', 'memoir'],
    ['nonfiction', 'non-fiction'],
    ['non-fiction', 'non-fiction'],
    ['history', 'history'],
    ['poetry', 'poetry'],
    ['short stories', 'short stories'],
    ['humor', 'humor'],
    ['satire', 'humor'],
];

function normalizeOLSubjects(subjects) {
    if (!subjects || !subjects.length) return '';
    const seen = new Set();
    const genres = [];
    for (const subj of subjects) {
        const sl = subj.toLowerCase();
        for (const [frag, genre] of OL_SUBJECT_MAP) {
            if (sl.includes(frag) && !seen.has(genre)) {
                seen.add(genre);
                genres.push(genre);
            }
        }
        if (genres.length >= 4) break;
    }
    return genres.join(', ');
}

async function fetchMissingCovers() {
    const placeholders = document.querySelectorAll('.book-cover-placeholder[data-book-id]');
    for (const placeholder of placeholders) {
        const bookId = placeholder.dataset.bookId;
        const title = placeholder.dataset.title;
        const author = placeholder.dataset.author;
        const book = allBooks.find(b => b.id == bookId);
        if (book && book.cover_url) continue;

        try {
            const meta = await fetchBookMetadata(title, author);
            if (meta.coverUrl) {
                const initials = getBookInitials(title);
                placeholder.outerHTML = `<img src="${meta.coverUrl}" class="book-cover" alt="Cover" onerror="this.outerHTML='<div class=book-cover-placeholder>${initials}</div>'">`;
                if (book) {
                    book.cover_url = meta.coverUrl;
                    if (!book.genre && meta.genre) book.genre = meta.genre;
                }
                saveCoverAndGenre(bookId, meta.coverUrl, meta.genre || '');
            }
        } catch (e) { /* silently fail */ }
    }
}

async function fetchBookMetadata(title, author) {
    try {
        const query = encodeURIComponent(`${title} ${author}`);
        const response = await fetch(`https://openlibrary.org/search.json?q=${query}&limit=1&fields=cover_i,subject`);
        const data = await response.json();
        if (data.docs && data.docs.length > 0) {
            const doc = data.docs[0];
            const coverUrl = doc.cover_i
                ? `https://covers.openlibrary.org/b/id/${doc.cover_i}-M.jpg`
                : null;
            const genre = normalizeOLSubjects(doc.subject || []);
            return { coverUrl, genre };
        }
    } catch (e) { }
    return { coverUrl: null, genre: '' };
}

async function fetchCoverUrl(title, author) {
    return (await fetchBookMetadata(title, author)).coverUrl;
}

async function saveCoverAndGenre(bookId, coverUrl, genre) {
    try {
        const body = { cover_url: coverUrl };
        if (genre) body.genre = genre;
        await fetch(`${API_URL}/books/${bookId}/cover`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
    } catch (e) { }
}

async function saveCoverUrl(bookId, coverUrl) {
    return saveCoverAndGenre(bookId, coverUrl, '');
}

// ============== COVER PICKER ==============
let coverPickerBookId = null;

function openCoverPicker(bookId) {
    const book = allBooks.find(b => b.id === bookId);
    if (!book) return;
    coverPickerBookId = bookId;
    const modal = document.getElementById('coverPickerModal');
    const title = document.getElementById('coverPickerTitle');
    const grid = document.getElementById('coverPickerGrid');
    const searchInput = document.getElementById('coverPickerSearch');

    title.textContent = `${book.title} by ${book.author}`;
    searchInput.value = `${book.title} ${book.author}`;
    grid.innerHTML = '<div class="cover-picker-loading"><div class="spinner"></div><p>Searching for covers...</p></div>';
    modal.classList.add('open');
    document.body.style.overflow = 'hidden';

    fetchCoverOptions(book.title, book.author);
}

function closeCoverPicker() {
    const modal = document.getElementById('coverPickerModal');
    modal.classList.remove('open');
    document.body.style.overflow = '';
    coverPickerBookId = null;
}

function coverPickerSearchAgain() {
    const query = document.getElementById('coverPickerSearch').value.trim();
    if (!query) return;
    const grid = document.getElementById('coverPickerGrid');
    grid.innerHTML = '<div class="cover-picker-loading"><div class="spinner"></div><p>Searching for covers...</p></div>';
    fetchCoverOptionsByQuery(query);
}

async function fetchCoverOptions(title, author) {
    const query = `${title} ${author}`;
    await fetchCoverOptionsByQuery(query);
}

async function fetchCoverOptionsByQuery(query) {
    const grid = document.getElementById('coverPickerGrid');
    try {
        const encoded = encodeURIComponent(query);
        const response = await fetch(`https://openlibrary.org/search.json?q=${encoded}&limit=20&fields=cover_i,title,author_name,edition_key,edition_count,first_publish_year,key`);
        const data = await response.json();
        const covers = [];
        const seenCoverIds = new Set();

        if (data.docs) {
            for (const doc of data.docs) {
                if (doc.cover_i && !seenCoverIds.has(doc.cover_i)) {
                    seenCoverIds.add(doc.cover_i);
                    covers.push({
                        coverId: doc.cover_i,
                        title: doc.title || '',
                        author: (doc.author_name || []).join(', '),
                        year: doc.first_publish_year || '',
                        editions: doc.edition_count || 1,
                        url: `https://covers.openlibrary.org/b/id/${doc.cover_i}-M.jpg`,
                        urlLarge: `https://covers.openlibrary.org/b/id/${doc.cover_i}-L.jpg`,
                    });
                }
            }

            // Also fetch edition-level covers for the top results
            const topDocs = data.docs.slice(0, 5);
            for (const doc of topDocs) {
                if (doc.edition_key && doc.edition_key.length > 0) {
                    try {
                        const edKeys = doc.edition_key.slice(0, 10).join(',');
                        const edResponse = await fetch(`https://openlibrary.org/api/get_multiple?keys=${doc.edition_key.slice(0, 8).map(k => '/books/' + k).join(',')}&fields=covers,title,publishers,publish_date`);
                        // Use a simpler approach: fetch editions via search
                    } catch (e) { /* skip edition fetch errors */ }
                }
            }
        }

        if (covers.length === 0) {
            grid.innerHTML = '<div class="cover-picker-empty">No covers found. Try a different search.</div>';
            return;
        }

        grid.innerHTML = covers.map((c, i) => `
            <div class="cover-option" onclick="selectCover('${c.url}')">
                <img src="${c.url}" alt="Cover option"
                     onerror="this.parentElement.style.display='none'"
                     loading="lazy">
                <div class="cover-option-info">
                    <div class="cover-option-title">${escapeHtml(c.title)}</div>
                    ${c.author ? `<div class="cover-option-author">${escapeHtml(c.author)}</div>` : ''}
                    ${c.year ? `<div class="cover-option-year">${c.year}</div>` : ''}
                </div>
            </div>
        `).join('');
    } catch (e) {
        grid.innerHTML = '<div class="cover-picker-empty">Error searching for covers. Please try again.</div>';
    }
}

async function selectCover(coverUrl) {
    if (!coverPickerBookId) return;
    const bookId = coverPickerBookId;
    const book = allBooks.find(b => b.id === bookId);

    // Update the cover in the UI immediately
    const bookItem = document.getElementById(`book-item-${bookId}`);
    if (bookItem) {
        const wrapper = bookItem.querySelector('.cover-wrapper');
        if (wrapper) {
            const initials = getBookInitials(book ? book.title : '');
            wrapper.innerHTML = `
                <img src="${escapeHtml(coverUrl)}" class="book-cover" alt="Cover"
                     onerror="this.outerHTML='<div class=book-cover-placeholder>${initials}</div>'">
                <div class="cover-edit-badge"><svg viewBox="0 0 24 24" width="10" height="10" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3a2.828 2.828 0 114 4L7.5 20.5 2 22l1.5-5.5L17 3z"/></svg></div>`;
        }
    }

    // Update local data
    if (book) book.cover_url = coverUrl;

    // Save to backend
    await saveCoverUrl(bookId, coverUrl);
    toast('Cover updated', 'success');
    closeCoverPicker();
}

// Close modal on escape key or backdrop click
document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
        const modal = document.getElementById('coverPickerModal');
        if (modal && modal.classList.contains('open')) closeCoverPicker();
    }
});

// ============== SUGGESTIONS ==
async function getSuggestions() {
    const btn = document.getElementById('getSuggestionsBtn');
    const numSuggestions = document.getElementById('numSuggestions').value;

    btn.disabled = true;
    btn.textContent = 'Getting suggestions...';

    try {
        const response = await fetch(`${API_URL}/suggestions?num=${numSuggestions}`);
        const data = await response.json();
        const container = document.getElementById('suggestionsContainer');

        if (data.success) {
            if (data.suggestions.length === 0) {
                container.innerHTML = `<div class="alert alert-info">No suggestions available at this time.</div>`;
            } else {
                container.innerHTML = `<div style="margin-top: 20px;">
                    ${data.suggestions.map((s, i) => `
                        <div class="suggestion-card" id="suggestion-${i}" data-title="${escapeHtml(s.title || '')}" data-author="${escapeHtml(s.author || '')}">
                            <div class="suggestion-title">${escapeHtml(s.title || 'Unknown Title')}</div>
                            <div class="suggestion-author">by ${escapeHtml(s.author || 'Unknown Author')}</div>
                            ${s.summary ? `<div class="suggestion-summary">${escapeHtml(s.summary)}</div>` : ''}
                            ${s.reason ? `<div class="suggestion-reason">${escapeHtml(s.reason)}</div>` : ''}
                            <div class="suggestion-actions">
                                <button class="add-to-library-btn" onclick="addSuggestionToLibrary(${i})">Add to Reading List</button>
                                <button class="reject-btn" onclick="rejectSuggestion(${i})">Not Interested</button>
                            </div>
                        </div>
                    `).join('')}
                </div>`;
            }
            toast(`Got ${data.suggestions.length} suggestions`, 'success');
        } else {
            toast(data.error || 'Error getting suggestions', 'error');
            container.innerHTML = '';
        }
    } catch (error) {
        toast('Error: ' + error.message, 'error');
        document.getElementById('suggestionsContainer').innerHTML = '';
    } finally {
        btn.disabled = false;
        btn.textContent = 'Get Suggestions';
    }
}

async function addSuggestionToLibrary(index) {
    const card = document.getElementById(`suggestion-${index}`);
    const title = card.dataset.title;
    const author = card.dataset.author;
    const btn = card.querySelector('.add-to-library-btn');
    btn.disabled = true;
    btn.textContent = 'Adding...';

    try {
        const response = await fetch(`${API_URL}/suggestions/add`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, author }),
        });
        const data = await response.json();

        if (data.success) {
            card.classList.add('added');
            card.querySelector('.suggestion-actions').innerHTML =
                `<div class="alert alert-success" style="margin: 0; text-align: center;">Added to your reading list</div>`;
            toast(`Added "${title}"`, 'success');
            loadStats();
            loadBooks();
        } else {
            btn.disabled = false;
            btn.textContent = 'Add to Reading List';
            toast(data.error || 'Failed to add book', 'error');
        }
    } catch (error) {
        btn.disabled = false;
        btn.textContent = 'Add to Reading List';
        toast('Error: ' + error.message, 'error');
    }
}

async function rejectSuggestion(index) {
    const card = document.getElementById(`suggestion-${index}`);
    const title = card.dataset.title;
    const author = card.dataset.author;
    const btn = card.querySelector('.reject-btn');
    btn.disabled = true;
    btn.textContent = 'Rejecting...';

    try {
        const response = await fetch(`${API_URL}/suggestions/reject`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, author }),
        });
        const data = await response.json();

        if (data.success) {
            card.classList.add('rejected');
            card.querySelector('.suggestion-actions').innerHTML =
                `<div class="alert" style="margin: 0; text-align: center; background: var(--danger-light); color: var(--danger);">Won't suggest this again</div>`;
        } else {
            btn.disabled = false;
            btn.textContent = 'Not Interested';
        }
    } catch (error) {
        btn.disabled = false;
        btn.textContent = 'Not Interested';
    }
}

// ============== LOAD STATS ==============
async function loadStats() {
    try {
        const response = await fetch(`${API_URL}/stats`);
        const data = await response.json();
        if (data.success && data.stats) {
            document.getElementById('totalBooks').textContent = data.stats.total_books;
            document.getElementById('readBooks').textContent = data.stats.read;
            document.getElementById('toReadBooks').textContent = data.stats.to_read;
            document.getElementById('currentlyReadingBooks').textContent = data.stats.currently_reading;
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// ====================================================================
//  ADMIN MODE — Spreadsheet-style database editor
// ====================================================================

async function adminRefresh() {
    try {
        const response = await fetch(`${API_URL}/books`);
        const data = await response.json();
        if (data.success) {
            adminBooks = data.books;
            adminSelected.clear();
            adminRender();
        }
    } catch (error) {
        toast('Failed to load admin data', 'error');
    }
}

function adminSearch() {
    adminSearchQuery = document.getElementById('adminSearchInput').value.toLowerCase().trim();
    adminRender();
}

function adminSort(col) {
    if (adminSortCol === col) {
        adminSortDir = adminSortDir === 'asc' ? 'desc' : 'asc';
    } else {
        adminSortCol = col;
        adminSortDir = 'asc';
    }
    adminRender();
}

function getAdminFilteredBooks() {
    let books = [...adminBooks];

    if (adminSearchQuery) {
        books = books.filter(b =>
            (b.title || '').toLowerCase().includes(adminSearchQuery) ||
            (b.author || '').toLowerCase().includes(adminSearchQuery) ||
            (b.genre || '').toLowerCase().includes(adminSearchQuery) ||
            (b.status || '').toLowerCase().includes(adminSearchQuery) ||
            String(b.id).includes(adminSearchQuery)
        );
    }

    const col = adminSortCol;
    const mult = adminSortDir === 'desc' ? -1 : 1;
    const dateFields = new Set(['read_date', 'date_added']);
    books.sort((a, b) => {
        if (col === 'id') return (Number(a[col] ?? 0) - Number(b[col] ?? 0)) * mult;
        if (dateFields.has(col)) {
            const va = parseDateVal(String(a[col] || ''));
            const vb = parseDateVal(String(b[col] || ''));
            if (va === null && vb === null) return 0;
            if (va === null) return 1;
            if (vb === null) return -1;
            return (va - vb) * mult;
        }
        let va = String(a[col] ?? '').toLowerCase();
        let vb = String(b[col] ?? '').toLowerCase();
        if (va < vb) return -1 * mult;
        if (va > vb) return 1 * mult;
        return 0;
    });

    return books;
}

function adminRender() {
    const books = getAdminFilteredBooks();
    const tbody = document.getElementById('adminTableBody');

    document.querySelectorAll('.admin-table .sort-icon').forEach(icon => {
        icon.classList.remove('active');
        icon.textContent = '\u21D5';
    });
    const activeIcon = document.querySelector(`.sort-icon[data-col="${adminSortCol}"]`);
    if (activeIcon) {
        activeIcon.classList.add('active');
        activeIcon.textContent = adminSortDir === 'asc' ? '\u2191' : '\u2193';
    }

    document.getElementById('adminRecordCount').textContent =
        `${books.length} of ${adminBooks.length} records`;

    updateBulkBar();

    if (books.length === 0) {
        tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; padding: 40px; color: var(--text-muted);">No records found</td></tr>`;
        return;
    }

    tbody.innerHTML = books.map(book => {
        const isSelected = adminSelected.has(book.id);
        const statusClass = {
            'read': 'status-read',
            'to-read': 'status-to-read',
            'currently-reading': 'status-currently-reading',
        }[book.status] || '';

        return `<tr class="${isSelected ? 'selected' : ''}" data-id="${book.id}">
            <td class="checkbox-cell">
                <input type="checkbox" ${isSelected ? 'checked' : ''} onchange="adminToggleRow(${book.id}, this.checked)">
            </td>
            <td class="id-cell">${book.id}</td>
            <td class="editable" ondblclick="adminEditCell(this, ${book.id}, 'title')">
                <div class="cell-text">${escapeHtml(book.title)}</div>
            </td>
            <td class="editable" ondblclick="adminEditCell(this, ${book.id}, 'author')">
                <div class="cell-text">${escapeHtml(book.author)}</div>
            </td>
            <td class="status-cell editable" ondblclick="adminEditCell(this, ${book.id}, 'status')">
                <span class="status-badge ${statusClass}">${escapeHtml(book.status)}</span>
            </td>
            <td class="editable" ondblclick="adminEditCell(this, ${book.id}, 'read_date')">
                <div class="cell-text">${escapeHtml(book.read_date)}</div>
            </td>
            <td class="editable" ondblclick="adminEditCell(this, ${book.id}, 'genre')">
                <div class="cell-text">${escapeHtml(book.genre)}</div>
            </td>
            <td class="editable" ondblclick="adminEditCell(this, ${book.id}, 'date_added')">
                <div class="cell-text">${escapeHtml(book.date_added)}</div>
            </td>
            <td class="actions-cell">
                <button class="delete-btn" onclick="adminDeleteRow(${book.id})" style="padding: 4px 8px; font-size: 11px;" title="Delete">
                    <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>
                </button>
            </td>
        </tr>`;
    }).join('');
}

// ============== ADMIN: INLINE CELL EDITING ==============
function adminEditCell(td, bookId, field) {
    if (td.classList.contains('editing')) return;
    adminCommitEdit();

    const book = adminBooks.find(b => b.id === bookId);
    if (!book) return;

    const currentValue = book[field] ?? '';
    td.classList.add('editing');

    if (field === 'status') {
        td.innerHTML = `
            <select onchange="adminSaveCell(${bookId}, '${field}', this.value, this.parentElement)"
                    onblur="setTimeout(() => adminCommitEdit(), 150)"
                    onkeydown="if(event.key==='Escape') adminCommitEdit()">
                <option value="to-read" ${currentValue === 'to-read' ? 'selected' : ''}>to-read</option>
                <option value="currently-reading" ${currentValue === 'currently-reading' ? 'selected' : ''}>currently-reading</option>
                <option value="read" ${currentValue === 'read' ? 'selected' : ''}>read</option>
            </select>`;
        td.querySelector('select').focus();
    } else {
        td.innerHTML = `
            <input type="text" value="${escapeHtml(currentValue)}"
                   onblur="adminSaveCell(${bookId}, '${field}', this.value, this.parentElement)"
                   onkeydown="if(event.key==='Enter') this.blur(); if(event.key==='Escape') adminCommitEdit();">`;
        const input = td.querySelector('input');
        input.focus();
        input.select();
    }

    adminEditingCell = { td, bookId, field };
}

async function adminSaveCell(bookId, field, newValue, td) {
    const book = adminBooks.find(b => b.id === bookId);
    if (!book) return;

    const oldValue = book[field] ?? '';
    if (String(newValue).trim() === String(oldValue).trim()) {
        adminCommitEdit();
        return;
    }

    try {
        const payload = {};
        payload[field] = newValue.trim();

        const response = await fetch(`${API_URL}/books/${bookId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        const data = await response.json();

        if (data.success && data.book) {
            const idx = adminBooks.findIndex(b => b.id === bookId);
            if (idx >= 0) adminBooks[idx] = data.book;
            const aIdx = allBooks.findIndex(b => b.id === bookId);
            if (aIdx >= 0) allBooks[aIdx] = data.book;
            toast(`Updated ${field}`, 'success');
        } else {
            toast(data.error || 'Failed to save', 'error');
        }
    } catch (error) {
        toast('Save failed: ' + error.message, 'error');
    }

    adminEditingCell = null;
    adminRender();
    loadStats();
}

function adminCommitEdit() {
    if (!adminEditingCell) return;
    adminEditingCell = null;
    adminRender();
}

// ============== ADMIN: ROW SELECTION ==============
function adminToggleRow(bookId, checked) {
    if (checked) adminSelected.add(bookId);
    else adminSelected.delete(bookId);
    adminRender();
}

function adminToggleAll(checkbox) {
    const filtered = getAdminFilteredBooks();
    if (checkbox.checked) {
        filtered.forEach(b => adminSelected.add(b.id));
    } else {
        adminSelected.clear();
    }
    adminRender();
}

function updateBulkBar() {
    const bar = document.getElementById('bulkBar');
    if (adminSelected.size === 0) {
        bar.style.display = 'none';
        return;
    }
    bar.style.display = 'flex';
    bar.innerHTML = `
        <span class="count">${adminSelected.size} selected</span>
        <button class="delete-btn" onclick="adminBulkDelete()" style="width: auto; padding: 6px 14px; font-size: 12px;">
            Delete Selected
        </button>
        <button onclick="adminBulkStatus('read')" style="width: auto; padding: 6px 14px; font-size: 12px; background: var(--success);">
            Set: Read
        </button>
        <button onclick="adminBulkStatus('to-read')" style="width: auto; padding: 6px 14px; font-size: 12px; background: var(--warning);">
            Set: To Read
        </button>
        <button onclick="adminBulkStatus('currently-reading')" style="width: auto; padding: 6px 14px; font-size: 12px; background: var(--info);">
            Set: Reading
        </button>
        <div style="flex:1;"></div>
        <button class="deselect" onclick="adminSelected.clear(); adminRender();"
                style="width: auto; padding: 6px 14px; font-size: 12px;">
            Deselect All
        </button>`;
}

// ============== ADMIN: BULK OPERATIONS ==============
async function adminBulkDelete() {
    const count = adminSelected.size;
    if (!confirm(`Delete ${count} selected book${count !== 1 ? 's' : ''}? This cannot be undone.`)) return;

    try {
        const response = await fetch(`${API_URL}/books/bulk-delete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ids: [...adminSelected] }),
        });
        const data = await response.json();

        if (data.success) {
            toast(`Deleted ${data.deleted} books`, 'success');
            adminSelected.clear();
            await adminRefresh();
            loadBooks();
            loadStats();
        } else {
            toast(data.error || 'Bulk delete failed', 'error');
        }
    } catch (error) {
        toast('Error: ' + error.message, 'error');
    }
}

async function adminBulkStatus(newStatus) {
    const ids = [...adminSelected];
    let successes = 0;

    for (const id of ids) {
        try {
            const body = { status: newStatus };
            if (newStatus === 'read') {
                const today = new Date();
                body.read_date = `${String(today.getMonth() + 1).padStart(2, '0')}/${String(today.getDate()).padStart(2, '0')}/${today.getFullYear()}`;
            }
            const response = await fetch(`${API_URL}/books/${id}/status`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });
            const data = await response.json();
            if (data.success) successes++;
        } catch (e) { }
    }

    toast(`Updated ${successes} of ${ids.length} books to "${newStatus}"`, 'success');
    adminSelected.clear();
    await adminRefresh();
    loadBooks();
    loadStats();
}

// ============== ADMIN: ADD ROW ==============
function adminAddRow() {
    const tbody = document.getElementById('adminTableBody');

    if (document.getElementById('admin-new-row')) {
        document.getElementById('admin-new-row').querySelector('input')?.focus();
        return;
    }

    const newRow = document.createElement('tr');
    newRow.id = 'admin-new-row';
    newRow.className = 'admin-new-row';
    newRow.innerHTML = `
        <td class="checkbox-cell"></td>
        <td class="id-cell" style="color: var(--success); font-weight: bold;">NEW</td>
        <td><input type="text" placeholder="Title *" id="newRowTitle"></td>
        <td><input type="text" placeholder="Author *" id="newRowAuthor"></td>
        <td>
            <select id="newRowStatus">
                <option value="to-read">to-read</option>
                <option value="currently-reading">currently-reading</option>
                <option value="read">read</option>
            </select>
        </td>
        <td><input type="text" placeholder="MM/DD/YYYY" id="newRowReadDate"></td>
        <td><input type="text" placeholder="Genre" id="newRowGenre"></td>
        <td><input type="text" placeholder="YYYY-MM-DD" id="newRowDateAdded"></td>
        <td class="actions-cell" style="display: flex; gap: 4px;">
            <button onclick="adminSaveNewRow()" style="padding: 4px 8px; font-size: 11px; background: var(--success);">Save</button>
            <button onclick="document.getElementById('admin-new-row').remove()"
                    style="padding: 4px 8px; font-size: 11px; background: var(--bg-card-alt); color: var(--text-primary); border: 1px solid var(--border);">Cancel</button>
        </td>`;

    tbody.insertBefore(newRow, tbody.firstChild);
    document.getElementById('newRowTitle').focus();

    newRow.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') adminSaveNewRow();
        if (e.key === 'Escape') newRow.remove();
    });
}

async function adminSaveNewRow() {
    const title = document.getElementById('newRowTitle').value.trim();
    const author = document.getElementById('newRowAuthor').value.trim();
    const status = document.getElementById('newRowStatus').value;
    const readDate = document.getElementById('newRowReadDate').value.trim() || null;

    if (!title || !author) {
        toast('Title and author are required', 'error');
        return;
    }

    try {
        const response = await fetch(`${API_URL}/books`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, author, status, read_date: readDate }),
        });
        const data = await response.json();

        if (data.success) {
            toast(`Added "${title}"`, 'success');
            const row = document.getElementById('admin-new-row');
            if (row) row.remove();
            await adminRefresh();
            loadBooks();
            loadStats();
        } else {
            toast(data.error || 'Failed to add', 'error');
        }
    } catch (error) {
        toast('Error: ' + error.message, 'error');
    }
}

// ============== ADMIN: DELETE ROW ==============
async function adminDeleteRow(bookId) {
    const book = adminBooks.find(b => b.id === bookId);
    if (!confirm(`Delete "${book?.title || 'this book'}"?`)) return;

    try {
        const response = await fetch(`${API_URL}/books/${bookId}`, { method: 'DELETE' });
        const data = await response.json();

        if (data.success) {
            adminBooks = adminBooks.filter(b => b.id !== bookId);
            allBooks = allBooks.filter(b => b.id !== bookId);
            adminSelected.delete(bookId);
            toast('Row deleted', 'success');
            adminRender();
            loadStats();
        } else {
            toast(data.error || 'Failed to delete', 'error');
        }
    } catch (error) {
        toast('Error: ' + error.message, 'error');
    }
}

// ============== ADMIN: EXPORT ==============
function exportCSV() {
    window.open(`${API_URL}/books/export`, '_blank');
    toast('Downloading CSV export...', 'info');
}

// ====================================================================
//  CHAT ENGINE — Conversational Book Recommendations
// ====================================================================

let chatConversationId = null;
let chatIsLoading = false;

async function chatLoadConversations() {
    try {
        const response = await fetch(`${API_URL}/chat/conversations`);
        const data = await response.json();
        const list = document.getElementById('conversationList');

        if (data.success && data.conversations && data.conversations.length > 0) {
            list.innerHTML = data.conversations.map(c => `
                <div class="conversation-item ${c.id === chatConversationId ? 'active' : ''}"
                     onclick="chatLoadConversation('${c.id}')">
                    <span class="conv-title">${escapeHtml(c.title || 'Untitled')}</span>
                    <button class="conv-delete" onclick="event.stopPropagation(); chatDeleteConversation('${c.id}')" title="Delete">&times;</button>
                </div>
            `).join('');
        } else {
            list.innerHTML = '<div style="color: var(--text-muted); font-size: 13px; text-align: center; padding: 20px;">No conversations yet</div>';
        }
    } catch (e) {
        console.error('Failed to load conversations:', e);
    }
}

function getChatWelcomeHTML() {
    return `
        <div class="chat-welcome" id="chatWelcome">
            <div class="welcome-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
                </svg>
            </div>
            <h3>Your Personal Book Advisor</h3>
            <p>I know your reading history and tastes. Tell me what you're in the mood for, and I'll find your next perfect read through conversation.</p>
            <div class="chat-starters">
                <button class="chat-starter" onclick="chatSendStarter(this.textContent)">What should I read next?</button>
                <button class="chat-starter" onclick="chatSendStarter(this.textContent)">I want something like my recent reads</button>
                <button class="chat-starter" onclick="chatSendStarter(this.textContent)">I'm in the mood for something light</button>
                <button class="chat-starter" onclick="chatSendStarter(this.textContent)">Surprise me with something different</button>
                <button class="chat-starter" onclick="chatSendStarter(this.textContent)">What are my reading patterns?</button>
                <button class="chat-starter" onclick="chatSendStarter(this.textContent)">Find me a page-turner for vacation</button>
            </div>
        </div>`;
}

function chatNewConversation() {
    chatConversationId = null;
    const messagesEl = document.getElementById('chatMessages');
    messagesEl.innerHTML = getChatWelcomeHTML();
    document.getElementById('chatIntentBadge').style.display = 'none';
    document.getElementById('chatInput').value = '';
    chatLoadConversations();
}

function chatSendStarter(text) {
    document.getElementById('chatInput').value = text;
    chatSend();
}

async function chatSend() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    if (!message || chatIsLoading) return;

    chatIsLoading = true;
    input.value = '';

    const sendBtn = document.getElementById('chatSendBtn');
    sendBtn.disabled = true;
    sendBtn.textContent = '...';

    const welcome = document.getElementById('chatWelcome');
    if (welcome) welcome.remove();

    const messagesEl = document.getElementById('chatMessages');
    messagesEl.innerHTML += `
        <div class="chat-message user">
            <div class="avatar">You</div>
            <div class="chat-bubble">${escapeHtml(message)}</div>
        </div>`;

    messagesEl.innerHTML += `
        <div class="chat-message assistant" id="chatTyping">
            <div class="avatar">AI</div>
            <div class="chat-bubble">
                <div class="chat-typing">
                    <span></span><span></span><span></span>
                </div>
            </div>
        </div>`;

    messagesEl.scrollTop = messagesEl.scrollHeight;

    try {
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                conversation_id: chatConversationId,
            }),
        });
        const data = await response.json();

        const typing = document.getElementById('chatTyping');
        if (typing) typing.remove();

        if (data.success) {
            chatConversationId = data.conversation_id;

            const badge = document.getElementById('chatIntentBadge');
            if (data.intent) {
                const intentLabels = {
                    'recommendation': 'Recommending',
                    'context_response': 'Understanding',
                    'library_query': 'Library',
                    'book_chat': 'Chatting',
                    'off_topic': 'Off Topic',
                };
                badge.textContent = intentLabels[data.intent] || data.intent;
                badge.style.display = 'inline-block';
            }

            let responseHtml = formatChatResponse(data.response, data.suggestions || []);

            messagesEl.innerHTML += `
                <div class="chat-message assistant">
                    <div class="avatar">AI</div>
                    <div class="chat-bubble">${responseHtml}</div>
                </div>`;

            messagesEl.scrollTop = messagesEl.scrollHeight;
            chatLoadConversations();
        } else {
            messagesEl.innerHTML += `
                <div class="chat-message assistant">
                    <div class="avatar">AI</div>
                    <div class="chat-bubble">${escapeHtml(data.error || 'Something went wrong')}</div>
                </div>`;
        }
    } catch (error) {
        const typing = document.getElementById('chatTyping');
        if (typing) typing.remove();

        messagesEl.innerHTML += `
            <div class="chat-message assistant">
                <div class="avatar">AI</div>
                <div class="chat-bubble">Connection error. Please try again.</div>
            </div>`;
    } finally {
        chatIsLoading = false;
        sendBtn.disabled = false;
        sendBtn.textContent = 'Send';
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }
}

function formatChatResponse(text, suggestions) {
    let html = escapeHtml(text);

    if (suggestions && suggestions.length > 0) {
        html += '<div style="margin-top: 12px;">';
        suggestions.forEach((s) => {
            const safeTitle = escapeHtml(s.title || '');
            const safeAuthor = escapeHtml(s.author || '');
            html += `
                <div class="chat-suggestion">
                    <div class="chat-suggestion-title">${safeTitle}</div>
                    <div class="chat-suggestion-author">by ${safeAuthor}</div>
                    ${s.summary ? `<div style="font-size: 13px; color: var(--text-primary); margin-top: 6px;">${escapeHtml(s.summary)}</div>` : ''}
                    ${s.reason ? `<div style="font-size: 12px; color: var(--accent); font-style: italic; margin-top: 4px;">Why: ${escapeHtml(s.reason)}</div>` : ''}
                    <div class="chat-suggestion-actions">
                        <button class="add-to-library-btn" data-title="${safeTitle}" data-author="${safeAuthor}" onclick="chatAddToLibrary(this)">Add to Library</button>
                        <button class="reject-btn" data-title="${safeTitle}" data-author="${safeAuthor}" onclick="chatRejectSuggestion(this)">Pass</button>
                    </div>
                </div>`;
        });
        html += '</div>';
    }

    return html;
}

async function chatAddToLibrary(btn) {
    const title = btn.dataset.title;
    const author = btn.dataset.author;
    btn.disabled = true;
    btn.textContent = 'Adding...';
    try {
        const response = await fetch(`${API_URL}/suggestions/add`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, author }),
        });
        const data = await response.json();
        if (data.success) {
            btn.textContent = 'Added';
            btn.style.background = 'var(--success-light)';
            btn.style.color = 'var(--success)';
            toast(`Added "${title}"`, 'success');
            loadStats();
            loadBooks();
        } else {
            btn.textContent = data.error || 'Error';
            btn.disabled = false;
        }
    } catch (e) {
        btn.textContent = 'Add to Library';
        btn.disabled = false;
    }
}

async function chatRejectSuggestion(btn) {
    const title = btn.dataset.title;
    const author = btn.dataset.author;
    btn.disabled = true;
    try {
        await fetch(`${API_URL}/suggestions/reject`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, author }),
        });
        btn.textContent = 'Passed';
        btn.style.opacity = '0.5';
    } catch (e) {
        btn.disabled = false;
    }
}

async function chatLoadConversation(convId) {
    try {
        const response = await fetch(`${API_URL}/chat/conversations/${convId}`);
        const data = await response.json();

        if (data.success && data.conversation) {
            chatConversationId = convId;
            const messages = data.conversation.messages || [];
            const messagesEl = document.getElementById('chatMessages');
            messagesEl.innerHTML = '';

            messages.forEach(m => {
                const isUser = m.role === 'user';
                messagesEl.innerHTML += `
                    <div class="chat-message ${isUser ? 'user' : 'assistant'}">
                        <div class="avatar">${isUser ? 'You' : 'AI'}</div>
                        <div class="chat-bubble">${isUser ? escapeHtml(m.content) : formatChatResponse(m.content, m.suggestions || [])}</div>
                    </div>`;
            });

            messagesEl.scrollTop = messagesEl.scrollHeight;
            chatLoadConversations();
        }
    } catch (e) {
        toast('Failed to load conversation', 'error');
    }
}

async function chatDeleteConversation(convId) {
    if (!confirm('Delete this conversation?')) return;
    try {
        await fetch(`${API_URL}/chat/conversations/${convId}`, { method: 'DELETE' });
        if (chatConversationId === convId) {
            chatNewConversation();
        }
        chatLoadConversations();
        toast('Conversation deleted', 'success');
    } catch (e) {
        toast('Failed to delete', 'error');
    }
}

// ====================================================================
//  (Pagination removed — replaced by infinite scroll in renderBooks)
// ====================================================================

// ====================================================================
//  READER DNA PROFILE
// ====================================================================

let profileLoaded = false;

async function loadProfile() {
    const content = document.getElementById('profileContent');
    content.innerHTML = '<div class="profile-loading"><div class="spinner"></div><p style="margin-top:15px;">Analyzing your reading patterns...</p></div>';
    document.getElementById('buildProfileBtn').disabled = true;
    try {
        const response = await fetch(`${API_URL}/profile`);
        const data = await response.json();
        if (data.success) {
            renderProfile(data.profile);
            profileLoaded = true;
        } else {
            content.innerHTML = `<div class="alert alert-error">${escapeHtml(data.error || 'Could not build profile. Make sure you have read books in your library.')}</div>`;
        }
    } catch (e) {
        content.innerHTML = `<div class="alert alert-error">Error: ${escapeHtml(e.message)}</div>`;
    } finally {
        document.getElementById('buildProfileBtn').disabled = false;
        document.getElementById('buildProfileBtn').textContent = 'Refresh Profile';
    }
}

function renderProfile(p) {
    const content = document.getElementById('profileContent');
    const genreDist = (p.genre_distribution && p.genre_distribution.distribution) || [];
    const authors = (p.author_analysis && p.author_analysis.favorite_authors) || [];
    const pace = p.reading_pace || {};
    const recency = p.recency_profile || {};
    const series = p.series_preference || {};
    const stats = p.library_stats || {};

    let html = `<div class="profile-summary-box">${escapeHtml(p.summary || '')}</div>`;
    html += `<div class="profile-grid">`;

    // Genre distribution card
    if (genreDist.length > 0) {
        const barsHtml = genreDist.slice(0, 10).map(([genre, count, pct]) => `
            <div class="genre-bar-row">
                <span class="genre-bar-label" title="${escapeHtml(genre)}">${escapeHtml(genre)}</span>
                <div class="genre-bar-track"><div class="genre-bar-fill" style="width:${Math.round(pct)}%"></div></div>
                <span class="genre-bar-pct">${Math.round(pct)}%</span>
            </div>`).join('');
        html += `<div class="profile-card"><h3>Genre Distribution</h3>${barsHtml}</div>`;
    }

    // Favorite authors card
    const userFavs = (p.author_analysis && p.author_analysis.user_favorites) || [];
    const allReadAuths = (p.author_analysis && p.author_analysis.all_read_authors) || [];
    window._profileAllAuthors = allReadAuths;
    window._profileFavAuthors = [...userFavs];

    const favItemsHtml = userFavs.length > 0
        ? userFavs.map(a => `
            <div class="profile-author-item">
                <span>${escapeHtml(a)}</span>
                <span class="profile-badge">Favorite</span>
            </div>`).join('')
        : `<p style="font-size:13px;color:var(--text-muted);margin:0 0 6px;">No favorites set &mdash; pick up to 3 below.</p>`;

    html += `<div class="profile-card">
        <h3>Favorite Authors</h3>
        ${favItemsHtml}
        <button class="secondary" onclick="toggleFavPicker()" style="width:auto;padding:5px 12px;font-size:12px;margin-top:8px;">
            ${userFavs.length > 0 ? 'Edit Favorites' : 'Set Favorites'}
        </button>
        <div id="favPickerPanel" style="display:none;margin-top:12px;border-top:1px solid var(--border);padding-top:12px;">
            <p style="font-size:12px;color:var(--text-muted);margin:0 0 6px;">Select up to 3 &mdash; these replace computed guesses in recommendations.</p>
            <input id="favSearchInput" type="text" placeholder="Search authors..."
                   oninput="renderFavPicker()"
                   style="width:100%;padding:5px 8px;font-size:12px;border:1px solid var(--border);border-radius:var(--radius-sm);margin-bottom:6px;box-sizing:border-box;">
            <div id="favPickerList" style="max-height:190px;overflow-y:auto;border:1px solid var(--border);border-radius:var(--radius-sm);padding:4px;"></div>
            <div style="margin-top:8px;display:flex;align-items:center;gap:10px;">
                <span id="favSelectedCount" style="font-size:12px;color:var(--text-muted);">0/3 selected</span>
                <button id="saveFavBtn" onclick="saveFavoriteAuthors()" style="width:auto;padding:5px 12px;font-size:12px;">Save Favorites</button>
            </div>
        </div>
    </div>`;

    // Reading pace card
    html += `<div class="profile-card"><h3>Reading Pace</h3>
        <div class="profile-stat-row"><span class="profile-stat-label">Pace</span><span class="profile-stat-value">${escapeHtml(pace.description || 'N/A')}</span></div>
        ${pace.books_per_month != null ? `<div class="profile-stat-row"><span class="profile-stat-label">Books/month</span><span class="profile-stat-value">${Number(pace.books_per_month).toFixed(1)}</span></div>` : ''}
    </div>`;

    // Recent interests card
    if (recency.recent_genres && recency.recent_genres.length > 0) {
        const recentGenres = recency.recent_genres.slice(0, 8).map(g => `<span class="recent-tag">${escapeHtml(g)}</span>`).join('');
        const recentAuthors = (recency.recent_authors || []).slice(0, 5)
            .map(a => `<span class="recent-tag">${escapeHtml(a)}</span>`).join('');
        html += `<div class="profile-card"><h3>Recent Interests</h3>
            <div style="margin-bottom:10px;"><strong style="font-size:12px;color:var(--text-muted);display:block;margin-bottom:4px;">GENRES</strong>${recentGenres}</div>
            ${recentAuthors ? `<div><strong style="font-size:12px;color:var(--text-muted);display:block;margin-bottom:4px;">AUTHORS</strong>${recentAuthors}</div>` : ''}
        </div>`;
    }

    // Author loyalty card
    const loyalty = p.author_analysis || {};
    html += `<div class="profile-card"><h3>Reading Patterns</h3>
        <div class="profile-stat-row"><span class="profile-stat-label">Unique authors</span><span class="profile-stat-value">${loyalty.total_unique_authors || 0}</span></div>
        <div class="profile-stat-row"><span class="profile-stat-label">Author loyalty</span><span class="profile-stat-value">${loyalty.loyalty_score != null ? Math.round(loyalty.loyalty_score * 100) + '%' : 'N/A'}</span></div>
        <div class="profile-stat-row"><span class="profile-stat-label">Discovery rate</span><span class="profile-stat-value">${loyalty.one_hit_authors_pct != null ? Math.round(loyalty.one_hit_authors_pct) + '%' : 'N/A'} read once</span></div>
    </div>`;

    // Series preference card
    if (series.description) {
        let seriesHtml = `<div class="profile-stat-row"><span class="profile-stat-label">Preference</span><span class="profile-stat-value" style="max-width:180px;text-align:right;font-size:12px;">${escapeHtml(series.description)}</span></div>`;
        if (series.active_series && series.active_series.length > 0) {
            seriesHtml += `<div style="margin-top:10px;font-size:12px;color:var(--text-muted);font-weight:600;">LIKELY IN A SERIES</div>`;
            series.active_series.slice(0, 3).forEach(s => {
                seriesHtml += `<div class="profile-stat-row" style="flex-direction:column;align-items:flex-start;gap:2px;">
                    <span style="font-weight:600;">${escapeHtml(s.author || '')}</span>
                    <span style="color:var(--text-muted);font-size:12px;">${escapeHtml((s.titles || []).slice(0, 3).join(', '))}</span>
                </div>`;
            });
        }
        html += `<div class="profile-card"><h3>Series vs Standalone</h3>${seriesHtml}</div>`;
    }

    // Library stats
    if (Object.keys(stats).length > 0) {
        const statsHtml = Object.entries(stats).map(([k, v]) =>
            `<div class="profile-stat-row"><span class="profile-stat-label">${escapeHtml(k.replace(/_/g, ' '))}</span><span class="profile-stat-value">${escapeHtml(String(v))}</span></div>`
        ).join('');
        html += `<div class="profile-card"><h3>Library Stats</h3>${statsHtml}</div>`;
    }

    html += `</div>`;
    content.innerHTML = html;
}

// ====================================================================
//  FAVORITE AUTHORS PICKER (Reader DNA tab)
// ====================================================================

function toggleFavPicker() {
    const panel = document.getElementById('favPickerPanel');
    if (!panel) return;
    const opening = panel.style.display === 'none';
    panel.style.display = opening ? 'block' : 'none';
    if (opening) {
        const searchEl = document.getElementById('favSearchInput');
        if (searchEl) searchEl.value = '';
        renderFavPicker();
    }
}

function renderFavPicker() {
    const listEl = document.getElementById('favPickerList');
    if (!listEl) return;
    const search = (document.getElementById('favSearchInput')?.value || '').toLowerCase();
    const all = window._profileAllAuthors || [];
    const favs = window._profileFavAuthors || [];
    const filtered = search ? all.filter(a => a.toLowerCase().includes(search)) : all;
    listEl.innerHTML = filtered.map(a => {
        const sel = favs.includes(a);
        const dis = !sel && favs.length >= 3;
        return `<label style="display:flex;align-items:center;padding:4px 8px;cursor:${dis ? 'not-allowed' : 'pointer'};border-radius:var(--radius-sm);${sel ? 'background:var(--bg-card-alt);font-weight:500;' : ''}opacity:${dis ? '0.45' : '1'};">
            <input type="checkbox" data-author="${escapeHtml(a)}" ${sel ? 'checked' : ''} ${dis ? 'disabled' : ''}
                   onchange="toggleFavAuthor(this)" style="margin-right:8px;flex-shrink:0;">
            <span style="font-size:13px;">${escapeHtml(a)}</span>
        </label>`;
    }).join('');
    const countEl = document.getElementById('favSelectedCount');
    if (countEl) countEl.textContent = `${favs.length}/3 selected`;
}

function toggleFavAuthor(el) {
    const name = el.dataset.author;
    if (!name) return;
    if (el.checked) {
        if ((window._profileFavAuthors || []).length < 3) {
            window._profileFavAuthors = window._profileFavAuthors || [];
            window._profileFavAuthors.push(name);
        } else {
            el.checked = false;
            return;
        }
    } else {
        window._profileFavAuthors = (window._profileFavAuthors || []).filter(a => a !== name);
    }
    renderFavPicker();
}

async function saveFavoriteAuthors() {
    const btn = document.getElementById('saveFavBtn');
    if (!btn) return;
    btn.disabled = true;
    btn.textContent = 'Saving...';
    try {
        const resp = await fetch(`${API_URL}/settings/favorite-authors`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ favorite_authors: window._profileFavAuthors || [] }),
        });
        const data = await resp.json();
        if (data.success) {
            btn.textContent = 'Saved';
            setTimeout(loadProfile, 900);
        } else {
            btn.textContent = 'Error — try again';
            btn.disabled = false;
        }
    } catch (e) {
        btn.textContent = 'Error — try again';
        btn.disabled = false;
    }
}

// ====================================================================
//  REJECTED BOOKS MANAGEMENT
// ====================================================================

let rejectedLoaded = false;

function toggleRejected(headerEl) {
    const body = document.getElementById('rejectedBody');
    const chevron = document.getElementById('rejectedChevron');
    const isOpen = body.classList.toggle('open');
    chevron.classList.toggle('open', isOpen);
    if (isOpen && !rejectedLoaded) {
        loadRejected();
    }
}

async function loadRejected() {
    const el = document.getElementById('rejectedContent');
    if (!el) return;
    try {
        const response = await fetch(`${API_URL}/rejected`);
        const data = await response.json();
        if (data.success) {
            renderRejected(data.rejected || []);
            rejectedLoaded = true;
        }
    } catch (e) {
        if (el) el.innerHTML = '<div class="rejected-empty">Failed to load rejected books.</div>';
    }
}

function renderRejected(rejected) {
    const el = document.getElementById('rejectedContent');
    if (!el) return;
    if (rejected.length === 0) {
        el.innerHTML = '<div class="rejected-empty">No rejected books. When you click "Not Interested" on a suggestion, it appears here.</div>';
        return;
    }
    el.innerHTML = `<table class="rejected-table">
        <thead><tr><th>Title</th><th>Author</th><th>Rejected</th><th></th></tr></thead>
        <tbody>
            ${rejected.map(r => `<tr id="rejected-row-${r.id}">
                <td>${escapeHtml(r.title || '')}</td>
                <td>${escapeHtml(r.author || '')}</td>
                <td style="color:var(--text-muted);">${escapeHtml((r.rejected_date || '').split(' ')[0])}</td>
                <td><button class="unreject-btn" data-id="${r.id}" onclick="unrejectBook(${r.id}, this)">Restore</button></td>
            </tr>`).join('')}
        </tbody>
    </table>`;
}

async function unrejectBook(id, btn) {
    btn.disabled = true;
    btn.textContent = '...';
    try {
        const response = await fetch(`${API_URL}/rejected/${id}`, { method: 'DELETE' });
        const data = await response.json();
        if (data.success) {
            const row = document.getElementById(`rejected-row-${id}`);
            if (row) {
                row.style.transition = 'opacity 0.3s';
                row.style.opacity = '0';
                setTimeout(() => {
                    row.remove();
                    const tbody = document.querySelector('.rejected-table tbody');
                    if (tbody && tbody.children.length === 0) {
                        renderRejected([]);
                    }
                }, 300);
            }
            toast('Book restored — it may appear in future suggestions', 'success');
        } else {
            btn.disabled = false;
            btn.textContent = 'Restore';
            toast(data.error || 'Failed to restore', 'error');
        }
    } catch (e) {
        btn.disabled = false;
        btn.textContent = 'Restore';
        toast('Error: ' + e.message, 'error');
    }
}
