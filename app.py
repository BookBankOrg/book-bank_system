from datetime import date
import os
import sqlite3
import random
from datetime import datetime
from flask import Flask, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message

# Initialisation Flask
app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Config base de données
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'book_bank.db')
DB = "book_bank.db"

# Config mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'wachiranathanael7@gmail.com'
app.config['MAIL_PASSWORD'] = 'rkeymznwntobxbbe'

app.config['MAIL_DEFAULT_SENDER'] = 'wachiranathanael7@gmail.com'


mail = Mail(app)

import secrets

def generate_otp():
    return str(secrets.randbelow(899999) + 100000)  # Modif


def send_otp(email, otp):
    msg = Message(
        subject='🔐 Book Bank - OTP Verification Code',
        sender='wachiranathanael7@gmail.com',
        recipients=[email]
    )
    msg.body = f"""\
Hello,

Your One-Time Password (OTP) to access the Book Bank System is:

🔢 {otp}

Please enter this code within the next 10 minutes to complete your login.

If you did not request this code, please ignore this email.

Thank you,  
📚 Book Bank System  
👨‍💻 Developed by Amine Mimoun & Nathanael Wachira
"""
    mail.send(msg)



ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

def get_books():
    conn = sqlite3.connect(DB, timeout=5)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()
    conn.close()
    return books

@app.route("/")
def index():
    return render_template("index.html", user=session.get("user"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        student_id = request.form["student_id"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        conn = sqlite3.connect(DB, timeout=5)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO students (name, student_id, email, password) VALUES (?, ?, ?, ?)",
                           (name, student_id, email, password))
            conn.commit()
        except sqlite3.IntegrityError:
            flash("Email or student ID already exists", "error")
            return redirect(url_for("register"))
        conn.close()
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect(DB)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        # Assure-toi de vérifier contre user[4], qui est le mot de passe
        if user and check_password_hash(user[4], password):
            otp = generate_otp()
            session["pending_user"] = email
            session["otp"] = otp
            send_otp(email, otp)
            return redirect(url_for("verify_otp"))
        else:
            flash("Incorrect email or password.")
    return render_template("login.html")



@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("librarian", None)
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))

@app.route("/borrow", methods=["GET", "POST"])
def borrow():
    if "user" not in session:
        return redirect(url_for("login"))
    conn = sqlite3.connect(DB, timeout=5)
    cursor = conn.cursor()
    if request.method == "POST":
        email = session["user"]
        cursor.execute("SELECT id FROM students WHERE email = ?", (email,))
        student_id = cursor.fetchone()[0]
        book_id = int(request.form["book_id"])
        cursor.execute("SELECT available FROM books WHERE id = ?", (book_id,))
        book = cursor.fetchone()
        if book and book[0] == 1:
            borrow_date = date.today().isoformat()
            cursor.execute("INSERT INTO borrow (student_id, book_id, borrow_date) VALUES (?, ?, ?)",
                           (student_id, book_id, datetime.now().strftime('%Y-%m-%d')))
            cursor.execute("UPDATE books SET available = 0 WHERE id = ?", (book_id,))
            conn.commit()
        conn.close()
        return redirect(url_for("index"))
    else:
        cursor.execute("SELECT id, title, author FROM books WHERE available = 1")
        books = cursor.fetchall()
        conn.close()
        return render_template("borrow.html", books=books)

@app.route("/return", methods=["GET", "POST"])
def return_book():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB, timeout=5)
    cursor = conn.cursor()
    email = session["user"]
    cursor.execute("SELECT id FROM students WHERE email = ?", (email,))
    student_id = cursor.fetchone()[0]


    if request.method == "POST":
        borrow_id = int(request.form["borrow_id"])
        cursor.execute("SELECT book_id FROM borrow WHERE id = ?", (borrow_id,))
        book = cursor.fetchone()
        return_date = date.today().isoformat()
        cursor.execute("UPDATE borrow SET return_date = ? WHERE id = ?", (return_date, borrow_id))
        if book:
            cursor.execute("UPDATE books SET available = 1 WHERE id = ?", (book[0],))
        conn.commit()
        conn.close()
        return redirect(url_for("return_book"))

    
    cursor.execute("""
        SELECT books.id, books.title, books.author, b.borrow_date,
               MAX(0, julianday('now') - julianday(b.borrow_date) - 7)*100 as fine,
                b.id  -- borrow id (utilisé pour le bouton return)
        FROM borrow b
        JOIN books ON b.book_id = books.id
        WHERE b.student_id = ? AND b.return_date IS NULL;
    """, (student_id,))
    borrowed_books = cursor.fetchall()
    conn.close()
    return render_template("return.html", borrowed_books=borrowed_books)

@app.route("/librarian/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["librarian"] = True
            flash("Librarian login successful", "success")
            return redirect(url_for("librarian_dashboard"))
        else:
            flash("Invalid librarian credentials", "error")
            return redirect(url_for("admin_login"))
    return render_template("librarian_login.html")

@app.route('/librarian/dashboard')
def librarian_dashboard():
    conn = sqlite3.connect(DB, timeout=5)
    c = conn.cursor()
    c.execute('SELECT * FROM books')
    books = c.fetchall()
    c.execute('''
        SELECT s.name, b.title, br.borrow_date, br.return_date
        FROM borrow br
        JOIN students s ON br.student_id = s.id
        JOIN books b ON br.book_id = b.id
    ''')
    records = [{'student_name': row[0], 'book_title': row[1], 'borrow_date': row[2], 'return_date': row[3]} for row in c.fetchall()]
    conn.close()
    return render_template('librarian_dashboard.html', books=books, records=records)

@app.route("/librarian/add", methods=["POST"])
def admin_add_book():
    if not session.get("librarian"):
        return redirect(url_for("admin_login"))
    title = request.form["title"]
    author = request.form["author"]
    conn = sqlite3.connect(DB, timeout=5)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO books (title, author) VALUES (?, ?)", (title, author))
    conn.commit()
    conn.close()
    flash("Book added successfully", "success")
    return redirect(url_for("librarian_dashboard"))

@app.route("/edit_book/<int:book_id>", methods=["GET", "POST"])
def edit_book(book_id):
    if not session.get("librarian"):
        return redirect(url_for("admin_login"))

    conn = sqlite3.connect(DB, timeout=5)
    cursor = conn.cursor()

    if request.method == "POST":
        title = request.form["title"]
        author = request.form["author"]
        cursor.execute("UPDATE books SET title = ?, author = ? WHERE id = ?", (title, author, book_id))
        conn.commit()
        conn.close()
        flash("Book updated successfully", "success")
        return redirect(url_for("librarian_dashboard"))

    cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
    book = cursor.fetchone()
    conn.close()
    return render_template("edit_book.html", book=book)

@app.route("/librarian/delete/<int:book_id>", methods=["POST"])
def admin_delete_book(book_id):
    if not session.get("librarian"):
        return redirect(url_for("admin_login"))
    conn = sqlite3.connect(DB, timeout=5)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()
    flash("Book deleted successfully", "success")
    return redirect(url_for("librarian_dashboard"))


@app.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    if request.method == "POST":
        entered_otp = request.form["otp"]
        if entered_otp == session.get("otp"):
            session["user"] = session.pop("pending_user")
            session.pop("otp", None)
            flash("Login successful.", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid OTP.", "danger")
    return render_template("verify_otp.html")

if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    app.run(debug=debug_mode)
