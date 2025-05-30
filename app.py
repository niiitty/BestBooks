from flask import Flask
from flask import render_template, request, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from difflib import get_close_matches

import sqlite3
import db
import librarian
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
    error = None
    username = request.form["username"]
    password1 = request.form["password1"]
    password2 = request.form["password2"]
    if password1 != password2:
        error = "Passwords must match"
        return render_template("register.html", error=error)
    password_hash = generate_password_hash(password1)

    try:
        sql = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
        db.execute(sql, [username, password_hash])
    except sqlite3.IntegrityError:
        error = "Username taken"
        return render_template("register.html", error=error)

    flash("Account created")
    return redirect(url_for("index"))

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/logging_in", methods=["POST"])
def logging_in():
    error = None
    username = request.form["username"]
    password = request.form["password"]

    try:
        sql = "SELECT password_hash FROM users WHERE username = ?"
        password_hash = db.query(sql, [username])[0][0]
    except IndexError:
        error = "User does not exist"
        return render_template("login.html", error=error)

    if check_password_hash(password_hash, password):
        session["username"] = username
        flash("Successfully logged in")
        return redirect(url_for("index"))
    else:
        error = "Username or password incorrect"
        return render_template("login.html", error=error)
    
@app.route("/logout")
def logout():
    del session["username"]
    flash("Successfully logged out")
    return redirect(url_for("index"))

# === adding/modifying/deleting books in database ===

@app.route("/add_book")
def add_book():
    return render_template("add_book.html", genres=librarian.genres)

@app.route("/add_book/upload", methods=["POST"])
def upload():
    title = request.form["title"]
    author = request.form["author"]
    publication_date = request.form.get("publication_date")
    genres = request.form.getlist("genres")

    book_id = librarian.add_book(title, author)

    if publication_date:
        librarian.add_attribute(book_id, "publication_date", publication_date)
    for genre in genres:
        librarian.add_attribute(book_id, "genre", genre)

    flash(f"\"{title}\" added to database")
    return redirect(url_for("index"))

@app.route("/search", methods=["GET", "POST"])
def search():
    suggestions = []
    query = ""
    if request.method == "POST":
        query = request.form["query"]
        exact = librarian.get_books_by_title(query)
        if exact:
            return redirect(url_for("book", book_id=exact[0]["book_id"]))
        
        candidates = librarian.get_similar_titles(query)
        titles = [c["title"] for c in candidates]
        matches = get_close_matches(query, titles, n=5, cutoff=0.3)

        title_map = {c["title"]: c for c in candidates}

        for title in matches:
            book = title_map[title]
            full = librarian.get_books_by_title(book["title"])
            if full:
                suggestions.append(full[0])

    return render_template("search.html", query=query, suggestions=suggestions)

@app.route("/book/<int:book_id>", methods=["GET", "POST"])
def book(book_id):
    base = librarian.get_book_by_book_id(book_id)
    title = base["title"]
    author = base["author"]
    
    attr = librarian.get_book_attributes(book_id)

    return render_template("book.html", book_id=book_id, title=title, author=author, attr=attr)

@app.route("/book/<int:book_id>/edit", methods=["GET", "POST"])
def edit_book(book_id):
    book = librarian.get_book_by_book_id(book_id)
    attr = librarian.get_book_attributes(book_id)

    if request.method == "GET":
        return render_template("edit_book.html", book=book, attr=attr, genres=librarian.genres)
    
    if request.method == "POST":
        title = request.form["title"]
        author = request.form["author"]
        publication_date = request.form.get("publication_date")
        genres = request.form.getlist("genres")

        if title != book["title"]:
            librarian.update_title(book_id, title)

        if author != book["author"]:
            librarian.update_author(book_id, author)

        if publication_date != attr.get("publication_date"):
            librarian.update_attribute(book_id, "publication_date", publication_date)

        if set(genres) != set(attr.get("genre", [])):
            librarian.update_attribute(book_id, "genre", genres)

        return redirect(url_for("book", book_id=book_id))
    
@app.route("/book/<int:book_id>/delete", methods=["GET", "POST"])
def delete_book(book_id):
    book = librarian.get_book_by_book_id(book_id)

    if request.method == "GET":
        return render_template("delete_book.html", book=book)
    
    if request.method == "POST":
        if request.form["delete"]:
            librarian.delete_book(book_id)
            flash(f"\"{book["title"]}\" successfully removed from database.")
            return redirect(url_for("index"))
        return redirect(url_for("book", book_id=book_id))
