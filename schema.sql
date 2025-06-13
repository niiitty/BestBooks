CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY, 
    username TEXT UNIQUE,
    password_hash TEXT,
    join_date TEXT
);

CREATE TABLE IF NOT EXISTS books (
    book_id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users,
    title TEXT,
    author TEXT
);

CREATE TABLE IF NOT EXISTS book_attributes (
    id INTEGER PRIMARY KEY,
    book_id INTEGER REFERENCES books,
    attribute_key TEXT,
    attribute_value TEXT
);

CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY,
    book_id INTEGER REFERENCES books,
    user_id INTEGER REFERENCES users,
    sent_at TEXT,
    rating INTEGER,
    title TEXT,
    content TEXT
);