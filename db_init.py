
import sqlite3

# Connexion à la base de données (ou création si elle n'existe pas)
conn = sqlite3.connect('book_bank.db')
cursor = conn.cursor()

# Création de la table books
cursor.execute('''
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    available INTEGER DEFAULT 1
)
''')

# Création de la table students
cursor.execute('''
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    student_id TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
''')

# Création de la table borrow
cursor.execute('''
CREATE TABLE IF NOT EXISTS borrow (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    book_id INTEGER NOT NULL,
    borrow_date TEXT NOT NULL,
    return_date TEXT,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (book_id) REFERENCES books(id)
)
''')

conn.commit()
conn.close()

print("Database initialized successfully.")
