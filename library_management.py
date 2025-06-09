from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime, timedelta
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database Initialization
def init_db():
    with sqlite3.connect('library.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS admins (id INTEGER PRIMARY KEY, username TEXT, password TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, username TEXT, password TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS books (id INTEGER PRIMARY KEY, title TEXT, author TEXT, isbn TEXT, status TEXT DEFAULT 'Available')''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS issued_books (id INTEGER PRIMARY KEY, book_id INTEGER, student_id INTEGER, issue_date TEXT, expiry_date TEXT, return_date TEXT)''')
        conn.commit()

# Landing Page
@app.route('/')
def index():
    return render_template('index.html')

# Admin Login
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect('library.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM admins WHERE username = ? AND password = ?', (username, password))
            admin = cursor.fetchone()
            if admin:
                session['admin_id'] = admin[0]
                return redirect(url_for('admin_dashboard'))
            flash('Invalid credentials', 'error')
    return render_template('admin_login.html')

# Admin Dashboard
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    return render_template('admin_dashboard.html')

# Create Admin
@app.route('/create_admin', methods=['GET', 'POST'])
def create_admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect('library.db') as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO admins (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            flash('Admin created successfully!', 'success')
        return redirect(url_for('admin_login'))
    return render_template('create_admin.html')

# Add Book
@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        isbn = request.form['isbn']
        with sqlite3.connect('library.db') as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO books (title, author, isbn) VALUES (?, ?, ?)', (title, author, isbn))
            conn.commit()
            flash('Book added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('add_book.html')

# View Books
@app.route('/view_books')
def view_books():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    with sqlite3.connect('library.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM books')
        books = cursor.fetchall()
    return render_template('view_books.html', books=books)

# Issue Book (Admin)
@app.route('/issue_book', methods=['GET', 'POST'])
def issue_book():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        book_id = request.form['book_id']
        student_id = request.form['student_id']
        issue_date = datetime.now().strftime('%Y-%m-%d')
        expiry_date = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
        with sqlite3.connect('library.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT status FROM books WHERE id = ?', (book_id,))
            status = cursor.fetchone()[0]
            if status == 'Available':
                cursor.execute('UPDATE books SET status = "Issued" WHERE id = ?', (book_id,))
                cursor.execute('INSERT INTO issued_books (book_id, student_id, issue_date, expiry_date) VALUES (?, ?, ?, ?)',
                               (book_id, student_id, issue_date, expiry_date))
                conn.commit()
                flash('Book issued successfully!', 'success')
            else:
                flash('Book is already issued!', 'error')
        return redirect(url_for('admin_dashboard'))
    return render_template('issue_book.html')

# View Issued Books
@app.route('/view_issued_books')
def view_issued_books():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    with sqlite3.connect('library.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT ib.id, b.title, s.username, ib.issue_date, ib.expiry_date, ib.return_date FROM issued_books ib JOIN books b ON ib.book_id = b.id JOIN students s ON ib.student_id = s.id')
        issued_books = cursor.fetchall()
    return render_template('view_issued_books.html', issued_books=issued_books)

# View Students
@app.route('/view_students')
def view_students():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    with sqlite3.connect('library.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM students')
        students = cursor.fetchall()
    return render_template('view_students.html', students=students)

# Student Register
@app.route('/student_register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect('library.db') as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO students (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            flash('Student registered successfully!', 'success')
        return redirect(url_for('student_login'))
    return render_template('student_register.html')

# Student Login
@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect('library.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM students WHERE username = ? AND password = ?', (username, password))
            student = cursor.fetchone()
            if student:
                session['student_id'] = student[0]
                return redirect(url_for('student_dashboard'))
            flash('Invalid credentials', 'error')
    return render_template('student_login.html')

# Student Dashboard
@app.route('/student_dashboard')
def student_dashboard():
    if 'student_id' not in session:
        return redirect(url_for('student_login'))
    student_id = session['student_id']
    with sqlite3.connect('library.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT ib.id, b.title, ib.issue_date, ib.expiry_date, ib.return_date FROM issued_books ib JOIN books b ON ib.book_id = b.id WHERE ib.student_id = ?', (student_id,))
        issued_books = cursor.fetchall()
    return render_template('student_dashboard.html', issued_books=issued_books)

# Search Books (For both Admin and Student)
@app.route('/search_books', methods=['GET', 'POST'])
def search_books():
    if 'admin_id' not in session and 'student_id' not in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        search_query = request.form['search_query']
        with sqlite3.connect('library.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM books WHERE title LIKE ? OR author LIKE ? OR isbn LIKE ?',
                           (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'))
            books = cursor.fetchall()
        return render_template('search_books.html', books=books)
    return render_template('search_books.html', books=[])

# Issue Book (Student)
@app.route('/student/issue_book/<int:book_id>', methods=['POST'])
def student_issue_book(book_id):
    if 'student_id' not in session:
        return redirect(url_for('student_login'))
    student_id = session['student_id']
    issue_date = datetime.now().strftime('%Y-%m-%d')
    expiry_date = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
    with sqlite3.connect('library.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT status FROM books WHERE id = ?', (book_id,))
        status = cursor.fetchone()[0]
        if status == 'Available':
            cursor.execute('UPDATE books SET status = "Issued" WHERE id = ?', (book_id,))
            cursor.execute('INSERT INTO issued_books (book_id, student_id, issue_date, expiry_date) VALUES (?, ?, ?, ?)',
                           (book_id, student_id, issue_date, expiry_date))
            conn.commit()
            flash('Book issued successfully!', 'success')
        else:
            flash('Book is already issued!', 'error')
    return redirect(url_for('student_dashboard'))

# Return Book (Student)
@app.route('/student/return_book/<int:issued_book_id>', methods=['POST'])
def student_return_book(issued_book_id):
    if 'student_id' not in session:
        return redirect(url_for('student_login'))
    return_date = datetime.now().strftime('%Y-%m-%d')
    with sqlite3.connect('library.db') as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE issued_books SET return_date = ? WHERE id = ?', (return_date, issued_book_id))
        cursor.execute('UPDATE books SET status = "Available" WHERE id = (SELECT book_id FROM issued_books WHERE id = ?)', (issued_book_id,))
        conn.commit()
        flash('Book returned successfully!', 'success')
    return redirect(url_for('student_dashboard'))

# Logout
@app.route('/logout')
def logout():
    session.pop('admin_id', None)
    session.pop('student_id', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)