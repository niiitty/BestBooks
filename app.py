from flask import Flask
from flask import render_template, request, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from difflib import get_close_matches

import sqlite3
import db
import config

app = Flask(__name__)
app.secret_key = config.secret_key

@app.route("/")
def index():
    return render_template("index.html")

# === account creation and logging in/out ===

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/create_account", methods=["POST"])
def create_account():
    username = request.form["username"]
    password1 = request.form["password1"]
    password2 = request.form["password2"]
    if password1 != password2:
        redirect(url_for("register"))
    password_hash = generate_password_hash(password1)

    try:
        sql = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
        db.execute(sql, [username, password_hash])
    except sqlite3.IntegrityError:
        return "ERROR: username taken"

    return "Account created"

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/logging_in", methods=["POST"])
def logging_in():
    username = request.form["username"]
    password = request.form["password"]

    try:
        sql = "SELECT password_hash FROM users WHERE username = ?"
        password_hash = db.query(sql, [username])[0][0]
    except IndexError:
        return "User does not exist"

    if check_password_hash(password_hash, password):
        session["username"] = username
        return redirect(url_for("index"))
    else:
        return "ERROR: username or password incorrect"
    
@app.route("/logout")
def logout():
    del session["username"]
    return redirect(url_for("index"))

# === adding books to database and shelf ===

def get_candidates(query):
    """Searches for books in the database with similar titles."""
    tokens = set(query)
    pattern_clauses = ["title LIKE ?"] * len(tokens)
    values = [f"%{token}%" for token in tokens]

    sql = f"""
    SELECT title FROM books
    WHERE {" OR ".join(pattern_clauses)}
    LIMIT 100
    """
    results = db.query(sql, values)
    return results

@app.route("/add_to_shelf", methods=["GET", "POST"])
def add_to_shelf():
    query = ""
    suggestions = []
    if request.method == "POST":
        query = request.form["query"]
        candidates = get_candidates(query)
        candidates = [c["title"] for c in candidates]
        suggestions = get_close_matches(query, candidates, n=5, cutoff=0.3)

    return render_template("add_to_shelf.html", query=query, suggestions=suggestions)

@app.route("/add_book")
def add_book():
    return render_template("add_book.html")

@app.route("/add_book/upload", methods=["POST"])
def upload():
    title = request.form["title"]
    author = request.form["author"]
    publication_date = request.form.get("publication_date")
    genres = request.form.getlist("genres")

    sql = "INSERT INTO books (title) VALUES (?)"
    db.execute(sql, (title,))
    book_id = db.last_insert_id()

    sql = "INSERT INTO book_attributes (book_id, attribute_key, attribute_value) VALUES (?, ?, ?)"

    if author:
        db.execute(sql, (book_id, "author", author))
    if publication_date:
        db.execute(sql, (book_id, "publication_date", publication_date))

    for genre in genres:
        db.execute(sql, (book_id, "genre", genre))

    return redirect("/")