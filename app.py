import sqlite3
import librarian
import users
import config
import math
import secrets

from flask import Flask
from flask import abort, flash, redirect, render_template, request, session, url_for
from difflib import get_close_matches
from functools import wraps

app = Flask(__name__)
app.secret_key = config.secret_key
librarian.db.initialize_database()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def check_csrf():
    if request.form["csrf_token"] != session["csrf_token"]:
        abort(403)
    
@app.route("/")
@app.route("/<int:page>")
def index(page=1):
    page_size = 10
    book_count = librarian.book_count()
    page_count = math.ceil(book_count / page_size)
    page_count = max(page_count, 1)

    if page < 1:
        return redirect(url_for("index", page=1))
    if page > page_count:
        return redirect(url_for("index", page=page_count))
    
    books = librarian.get_books(page, page_size)
    return render_template("index.html", books=books, page=page, page_count=page_count)

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
        session["csrf_token"] = secrets.token_hex(16)
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
    check_csrf()
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
        if genre not in librarian.genres:
            abort(403)
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
        titles = [c["title"].lower() for c in candidates]
        matches = get_close_matches(query.lower(), titles, n=10, cutoff=0.25)

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
    user = users.get_user(base["user_id"])
    reviews = librarian.get_reviews_by_book(book_id)
    stats = librarian.get_review_stats(book_id)

    return render_template("book.html", book_id=book_id, base=base, attr=attr, user=user, reviews=reviews, stats=stats)

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
        check_csrf()
        title = request.form["title"]
        if not title or len(title) > 100:
            abort(403)
        author = request.form["author"]
        if not author or len(author) > 100:
            abort(403)
        publication_date = request.form.get("publication_date")
        genres = request.form.getlist("genres")
        if not set(genres).issubset(librarian.genres):
            abort(403)

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
        check_csrf()
        if "delete" in request.form:
            librarian.delete_book(book_id)
            flash(f"\"{book['title']}\" successfully removed from database.")
            return redirect(url_for("index"))
        return redirect(url_for("book", book_id=book_id))

# === user profile ===

@app.route("/profile/<int:user_id>", methods=["GET", "POST"])
@app.route("/profile/<int:user_id>/<int:page>")
def profile(user_id, page=1):
    user = users.get_user(user_id)
    if not user:
        abort(404)

    page_size = 10
    book_count = librarian.book_count_of_user(user_id)
    page_count = math.ceil(book_count / page_size)
    page_count = max(page_count, 1)

    if page < 1:
        return redirect(url_for("profile", user_id=user_id, page=1))
    if page > page_count:
        return redirect(url_for("profile", user_id=user_id, page=page_count))
    
    books = librarian.get_books_by_user_id(user_id, page, page_size)

    return render_template(
        "profile.html",
        user_id=user_id,
        user=user,
        books=books,
        page=page,
        page_count=page_count,
        book_count=book_count
    )

# === reviews ===

@app.route("/book/<int:book_id>/add_review", methods=["GET", "POST"])
@login_required
def add_review(book_id):
    base = librarian.get_book_by_book_id(book_id)
    if not base:
        abort(404)
    review = librarian.get_review(book_id, session["user_id"])

    if request.method == "GET":
        return render_template("add_review.html", book_id=book_id, base=base, review=review)
    
    if request.method == "POST":
        check_csrf()
        rating = request.form["rating"]
        if int(rating) not in range(1, 6):  
            abort(403)
        review_title = request.form["title"]
        if len(review_title) > 100:
            abort(403)
        content = request.form["content"]
        if len(content) > 5000:
            abort(403)

        if not review:
            librarian.add_review(book_id, session["user_id"], rating, review_title, content)
            return redirect(url_for("book", book_id=book_id))
        
        for i in ["rating", "title", "content"]:
            if review[i] != request.form[i]:
                librarian.update_review(book_id, session["user_id"], i, request.form[i])

        return redirect(url_for("book", book_id=book_id))

@app.route("/book/<int:book_id>/<int:user_id>", methods=["GET"])
def review(book_id, user_id):
    book = librarian.get_book_by_book_id(book_id)
    if not book:
        abort(404)
    review = librarian.get_review(book_id, user_id)
    if not review:
        abort(404)
    review_writer = users.get_user(user_id)
    if not review_writer:
        abort(404)
    
    if request.method == "GET":
        return render_template("review.html", book=book, review=review, writer=review_writer)

@app.route("/book/<int:book_id>/<int:user_id>/delete", methods=["GET", "POST"])
@login_required
def delete_review(book_id, user_id):
    review = librarian.get_review(book_id, user_id)
    if not review:
        abort(404)
    book = librarian.get_book_by_book_id(book_id)
    
    if request.method == "GET":
        return render_template("delete_review.html", review=review, book=book)
    
    if request.method == "POST":
        check_csrf()
        if "delete" in request.form:
            librarian.delete_review(book_id, user_id)
            return redirect(url_for("book", book_id=book_id))

        return redirect(url_for("review", book_id=book_id, user_id=user_id))