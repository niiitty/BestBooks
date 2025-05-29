CREATE TABLE users (
    user_id INTEGER PRIMARY KEY, 
    username TEXT UNIQUE,
    password_hash TEXT
);

CREATE TABLE books (
    book_id INTEGER PRIMARY KEY,
    title TEXT,
    author TEXT
);

CREATE TABLE book_attributes (
    id INTEGER PRIMARY KEY,
    book_id INTEGER REFERENCES books,
    attribute_key TEXT,
    attribute_value TEXT
);

CREATE TABLE reviews (
    id INTEGER PRIMARY KEY,
    content TEXT,
    book_id INTEGER REFERENCES books,
    sent_at TEXT,
    user_id INTEGER REFERENCES users
);