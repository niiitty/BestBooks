from flask import Flask
from flask import abort, flash, redirect, render_template, request, session, url_for
from difflib import get_close_matches
from functools import wraps

import sqlite3
import librarian
import users
import config

app = Flask(__name__)
app.secret_key = config.secret_key

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

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
    if not username or not 6 <= len(username) <= 50:
        abort(403)
    password1 = request.form["password1"]
    password2 = request.form["password2"]
    if password1 != password2:
        error = "Passwords must match"
        return render_template("register.html", error=error, username=username)
    if not password1 or not 7 <= len(password1) <= 100:
        abort(403)
    try:
        users.create_user(username, password1)
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
        user_id = users.check_login(username, password)
    except IndexError:
        error = "User does not exist"
        return render_template("login.html", error=error)

    if user_id:
        session["user_id"] = user_id
        session["username"] = username
        flash("Successfully logged in")
        return redirect(url_for("index"))
    
    error = "Username or password incorrect"
    return render_template("login.html", error=error, username=username)
    
@app.route("/logout")
@login_required
def logout():
    del session["user_id"]
    del session["username"]
    flash("Successfully logged out")
    return redirect(url_for("index"))

# === adding/modifying/deleting books in database ===

@app.route("/add_book")
@login_required
def add_book():
    return render_template("add_book.html", genres=librarian.genres)

@app.route("/add_book/upload", methods=["POST"])
@login_required
def upload():
    title = request.form["title"]
    if not title or len(title) > 100:
        abort(403)
    author = request.form["author"]
    if not author or len(author) > 100:
        abort(403)
    publication_date = request.form.get("publication_date")
    genres = request.form.getlist("genres")
    user_id = session["user_id"]

    book_id = librarian.add_book(user_id, title, author)

    if publication_date:
        librarian.add_attribute(book_id, "publication_date", publication_date)
    for genre in genres:
        librarian.add_attribute(book_id, "genre", genre)

    flash(f"\"{title}\" added to database")
    return redirect(url_for("index"))

@app.route("/search", methods=["GET", "POST"])
@login_required
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
    if not base:
        abort(404)
    
    attr = librarian.get_book_attributes(book_id)

    return render_template("book.html", book_id=book_id, base=base, attr=attr)

@app.route("/book/<int:book_id>/edit", methods=["GET", "POST"])
@login_required
def edit_book(book_id):
    book = librarian.get_book_by_book_id(book_id)
    if not book:
        abort(404)
    if session["user_id"] != book["user_id"]:
        abort(403)

    attr = librarian.get_book_attributes(book_id)

    if request.method == "GET":
        return render_template("edit_book.html", book=book, attr=attr, genres=librarian.genres)
    
    if request.method == "POST":
        title = request.form["title"]
        if not title or len(title) > 100:
            abort(403)
        author = request.form["author"]
        if not author or len(author) > 100:
            abort(403)
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
@login_required
def delete_book(book_id):
    book = librarian.get_book_by_book_id(book_id)
    if not book:
        abort(404)
    if session["user_id"] != book["user_id"]:
        abort(403)

    if request.method == "GET":
        return render_template("delete_book.html", book=book)
    
    if request.method == "POST":
        if "delete" in request.form:
            librarian.delete_book(book_id)
            flash(f"\"{book['title']}\" successfully removed from database.")
            return redirect(url_for("index"))
        return redirect(url_for("book", book_id=book_id))
