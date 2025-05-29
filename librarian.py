import db
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
    """Searches for books in the database with similar titles."""
    tokens = set(query)
    pattern_clauses = ["title LIKE ?"] * len(tokens)
    values = [f"%{token}%" for token in tokens]

    sql = f"""
    SELECT book_id, title FROM books
    WHERE {" OR ".join(pattern_clauses)}
    LIMIT 100
    """
    return db.query(sql, values)

def get_book_attr(book_id: int) -> list[Row]:
    sql ="""SELECT atr.attribute_key AS key, atr.attribute_value AS value
            FROM book_attributes atr, books b
            WHERE atr.book_id = b.book_id
            AND b.book_id = ?
        """
    return db.query(sql, [book_id])

def get_books_by_title(title: str) -> list[Row]:
    sql = "SELECT * FROM books WHERE title = ?"
    return db.query(sql, [title])

def get_book_by_book_id(book_id: int) -> Row:
    sql = "SELECT * FROM books WHERE book_id = ?"
    return db.query(sql, [book_id])[0]
