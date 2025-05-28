import db

# TODO might not work properly with large databases due to limit 
def get_similar_titles(query):
    """Searches for books in the database with similar titles."""
    tokens = set(query)
    pattern_clauses = ["title LIKE ?"] * len(tokens)
    values = [f"%{token}%" for token in tokens]

    sql = f"""
    SELECT title FROM books
    WHERE {" OR ".join(pattern_clauses)}
    LIMIT 100
    """
    return db.query(sql, values)

def get_book_info(title):
    sql ="""SELECT atr.attribute_key AS key, atr.attribute_value AS value
            FROM book_attributes atr, books b
            WHERE atr.book_id = b.book_id
            AND b.title = ?
        """
    return db.query(sql, [title])

def get_book_title(query):
    sql = "SELECT title FROM books WHERE title = ?"
    return db.query(sql, [query])