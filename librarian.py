import db
from collections import defaultdict
from sqlite3 import Row

genres = sorted([
    "Adventure", "Biography", "Children's", "Classic", "Comedy", "Contemporary",
    "Crime", "Dystopian", "Fantasy", "Graphic Novel", "Historical Fiction",
    "History", "Horror", "LGBTQ+", "Memoir", "Mystery", "Non-fiction",
    "Philosophy", "Poetry", "Psychology", "Romance", "Science",
    "Science Fiction", "Self-help", "Short Stories", "Thriller",
    "Travel", "Young Adult", "Sports", "Manga"
])

def get_similar_titles(query: str) -> list[Row]:
    """Searches for books in the database with similar titles. Returns book_id, title, and author"""
    tokens = query.strip().split()
    pattern_clauses = ["title LIKE ?"] * len(tokens)
    values = [f"%{token}%" for token in tokens]

    sql = f"""
        SELECT book_id, title, author FROM books
        WHERE {" OR ".join(pattern_clauses)}
    """
    return db.query(sql, values)

def add_book(user_id, title, author):
    sql = "INSERT INTO books (user_id, title, author) VALUES (?, ?, ?)"
    db.execute(sql, (user_id, title, author))
    return db.last_insert_id()

def add_attribute(book_id, key, value):
    sql = "INSERT INTO book_attributes (book_id, attribute_key, attribute_value) VALUES (?, ?, ?)"
    db.execute(sql, (book_id, key, value))

def get_book_attributes(book_id: int) -> dict[Row, list]:
    """Returns dictionary of key-value pairs of a book's attributes."""

    sql = """
        SELECT attribute_key AS key, attribute_value AS value
        FROM book_attributes
        WHERE book_id = ?
    """
    query = db.query(sql, [book_id])

    attr_dict = defaultdict(list)
    for row in query:
        key, value = row["key"], row["value"]
        if key == "genre":
            attr_dict[key].append(value)
        else:
            if key not in attr_dict:
                attr_dict[key] = value

    return attr_dict

def get_books(page, page_size):
    sql = """
        SELECT book_id, title, author FROM books 
        GROUP BY book_id
        ORDER BY book_id DESC
        LIMIT ? OFFSET ?
    """
    limit = page_size
    offset = (page - 1) * page_size
    return db.query(sql, [limit, offset])

#TODO bug with same titles
def get_books_by_title(title: str) -> list[Row]:
    """Returns book_id, title, author of (multiple) books with the exact title."""
    sql = "SELECT book_id, title, author FROM books WHERE title = ?"
    return db.query(sql, [title])

def get_book_by_book_id(book_id: int) -> Row:
    """Returns user_id, book_id, title, author of a specific book."""
    sql = "SELECT user_id, book_id, title, author FROM books WHERE book_id = ?"
    result = db.query(sql, [book_id])
    return result[0] if result else None

def get_books_by_user_id(user_id: int, page, page_size) -> Row:
    """Returns book_id, title, author of (multiple) books associated with a certain user."""
    sql = """
        SELECT book_id, title, author FROM books 
        WHERE user_id = ?
        LIMIT ? OFFSET ?
    """
    
    limit = page_size
    offset = (page - 1) * page_size
    return db.query(sql, [user_id, limit, offset])

def update_title(book_id, title):
    sql = "UPDATE books SET title = ? WHERE book_id = ?"
    db.execute(sql, [title, book_id])

def update_author(book_id, author):
    sql = "UPDATE books SET author = ? WHERE book_id = ?"
    db.execute(sql, [author, book_id])  

def update_publication_date(book_id, publication_date):
    sql = "DELETE FROM book_attributes WHERE book_id = ? AND attribute_key = 'publication_date'"
    db.execute(sql, [book_id])

    sql = "INSERT INTO book_attributes (book_id, attribute_key, attribute_value) VALUES (?, 'publication_date', ?)"
    db.execute(sql, [book_id, publication_date])  

def update_genres(book_id, genres):
    sql = "DELETE FROM book_attributes WHERE book_id = ? AND attribute_key = 'genre'"
    db.execute(sql, [book_id])

    for genre in genres:
        sql = "INSERT INTO book_attributes (book_id, attribute_key, attribute_value) VALUES (?, 'genre', ?)"
        db.execute(sql, [book_id, genre])

def delete_book(book_id):
    sql = "DELETE FROM reviews WHERE book_id = ?"
    db.execute(sql, [book_id])

    sql = "DELETE FROM book_attributes WHERE book_id = ?"
    db.execute(sql, [book_id])
    
    sql = "DELETE FROM books WHERE book_id = ?"
    db.execute(sql, [book_id])

def book_count():
    sql = "SELECT COUNT(book_id) FROM books"
    return db.query(sql, [])[0]["COUNT(book_id)"]

def book_count_of_user(user_id):
    sql = "SELECT COUNT(book_id) FROM books WHERE user_id = ?"
    return db.query(sql, [user_id])[0]["COUNT(book_id)"]

def add_review(book_id, user_id, rating, title, content):
    sql = "INSERT INTO reviews (book_id, user_id, sent_at, rating, title, content) VALUES (?, ?, datetime('now', 'localtime'), ?, ?, ?)"
    db.execute(sql, [book_id, user_id, rating, title, content])

def get_reviews_by_book(book_id, page, page_size):
    """Returns a list of reviews: id, user_id, username, sent time, rating, and title."""
    sql = """
        SELECT r.id, r.user_id, u.username, r.sent_at, r.rating, r.title
        FROM reviews r
        JOIN users u ON r.user_id = u.user_id
        WHERE r.book_id = ?
        GROUP BY r.id
        ORDER BY r.id DESC
        LIMIT ? OFFSET ?
    """
    limit = page_size
    offset = (page - 1) * page_size
    return db.query(sql, [book_id, limit, offset])

def get_review_stats(book_id):
    """Returns total number of reviews and average rating for a book."""
    sql = """
        SELECT COUNT(id) AS review_count, ROUND(AVG(rating), 2) AS average_rating
        FROM reviews
        WHERE book_id = ?
    """
    result = db.query(sql, [book_id])
    return result[0] if result else None

def get_reviews_by_user(user_id):
    """Returns id, book_id, book title, send time (YYYY-MM-DD hh:mm:ss), rating, title of (multiple) reviews."""
    sql = """
        SELECT r.id, b.book_id, b.title, r.sent_at, r.rating, r.title
        FROM reviews r
        JOIN books b ON r.book_id = b.book_id
        WHERE user_id = ?
    """
    return db.query(sql, [user_id])

def get_review(book_id, user_id):
    """Returns rating, title, content of review."""
    sql = "SELECT rating, title, content FROM reviews WHERE book_id = ? AND user_id = ?"
    result = db.query(sql, [book_id, user_id])
    return result[0] if result else None

def update_review(book_id, user_id, key, value):
    if key not in ["rating", "title", "content"]:
        raise ValueError
    sql = f"UPDATE reviews SET {key} = ? WHERE book_id = ? AND user_id = ?"
    db.execute(sql, [value, book_id, user_id])

def delete_review(book_id, user_id):
    sql = "DELETE FROM reviews WHERE book_id = ? AND user_id = ?"
    db.execute(sql, [book_id, user_id])
