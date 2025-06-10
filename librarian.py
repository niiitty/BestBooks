import db
from collections import defaultdict
from sqlite3 import Row

genres = sorted([
    "Adventure", "Biography", "Children's", "Classic", "Comedy", "Contemporary",
    "Crime", "Dystopian", "Fantasy", "Graphic Novel", "Historical Fiction",
    "History", "Horror", "LGBTQ+", "Memoir", "Mystery", "Non-fiction",
    "Philosophy", "Poetry", "Psychology", "Romance", "Science",
    "Science Fiction", "Self-help", "Short Stories", "Thriller",
    "Travel", "Young Adult"
])

# TODO might not work properly with large databases due to limit 
def get_similar_titles(query) -> list[Row]:
    "Searches for books in the database with similar titles."
    tokens = set(query)
    pattern_clauses = ["title LIKE ?"] * len(tokens)
    values = [f"%{token}%" for token in tokens]

    sql = f"""
    SELECT book_id, title FROM books
    WHERE {" OR ".join(pattern_clauses)}
    LIMIT 100
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
    "Returns dictionary of key-value pairs of a book's attributes."

    sql = """SELECT attribute_key AS key, attribute_value AS value
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

def get_books():
    sql = """SELECT book_id, title, author FROM books 
            GROUP BY book_id
            ORDER BY book_id DESC"""
    return db.query(sql, [])

def get_books_by_title(title: str) -> list[Row]:
    "Returns book_id, title, author of (multiple) books with the exact title."
    sql = "SELECT book_id, title, author FROM books WHERE title = ?"
    return db.query(sql, [title])

def get_book_by_book_id(book_id: int) -> Row:
    "Returns user_id, book_id, title, author of a specific book."
    sql = "SELECT user_id, book_id, title, author FROM books WHERE book_id = ?"
    result = db.query(sql, [book_id])
    return result[0] if result else None

def get_books_by_user_id(user_id: int) -> Row:
    "Returns book_id, title, author of (multiple) books associated with a certain user."
    sql = "SELECT book_id, title, author FROM books WHERE user_id = ?"
    return db.query(sql, [user_id])

def update_title(book_id, title):
    sql = "UPDATE books SET title = ? WHERE book_id = ?"
    db.execute(sql, [title, book_id])

def update_author(book_id, author):
    sql = "UPDATE books SET author = ? WHERE book_id = ?"
    db.execute(sql, [author, book_id])  

def update_attribute(book_id, key, value):
    if isinstance(value, list):
        sql = "DELETE FROM book_attributes WHERE book_id = ? AND attribute_key = ?"
        db.execute(sql, [book_id, key])

        sql = "INSERT INTO book_attributes (book_id, attribute_key, attribute_value) VALUES (?, ?, ?)"
        for v in value:
            db.execute(sql, [book_id, key, v]) 
    else:
        sql = "SELECT attribute_value FROM book_attributes WHERE book_id = ? AND attribute_key = ?"
        existing = db.query(sql,[book_id, key])

        if existing:
            if existing[0]["attribute_value"] != value:
                sql = "UPDATE book_attributes SET attribute_value = ? WHERE book_id = ? AND attribute_key = ?"
                db.execute(sql, [value, book_id, key])
        else:
            sql = "INSERT INTO book_attributes (book_id, attribute_key, attribute_value) VALUES (?, ?, ?)"
            db.execute(sql, [book_id, key, value])

def delete_book(book_id):
    sql = "DELETE FROM book_attributes WHERE book_id = ?"
    db.execute(sql, [book_id])
    
    sql = "DELETE FROM books WHERE book_id = ?"
    db.execute(sql, [book_id])
