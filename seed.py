import random
import sqlite3
from werkzeug.security import generate_password_hash
from flask import g

def get_connection():
    con = sqlite3.connect("database.db")
    con.execute("PRAGMA foreign_keys = ON")
    con.row_factory = sqlite3.Row
    return con

def execute(sql, params=[]):
    con = get_connection()
    result = con.execute(sql, params)
    con.commit()
    g.last_insert_id = result.lastrowid
    con.close()

def last_insert_id():
    return g.last_insert_id

user_count = 1000
book_count = 10**6

con = get_connection()
cur = con.cursor()

print("Generating user data...")
pswd = generate_password_hash("password")
user_data = [
    ("user" + str(i), pswd)
    for i in range(1, user_count + 1)
]
cur.executemany(
    "INSERT INTO users (username, password_hash, join_date) VALUES (?, ?, date('now'))",
    user_data
)
print("User data generated!")

print("Genereating book data...")
book_data = [
    (random.randint(1, user_count), f"book {i}", f"author{i * 2}")
    for i in range(1, book_count + 1)
]
cur.executemany(
    "INSERT INTO books (user_id, title, author) VALUES (?, ?, ?)",
    book_data
)
print("Book data generated!")

print("Generating review data...")
review_data = [
    (book_count, user, random.randint(1, 5))
    for user in range(1, user_count + 1)
]
cur.executemany(
    "INSERT INTO reviews (book_id, user_id, rating) VALUES (?, ?, ?)",
    review_data
)
print("Review data generated!")

print("Done!")
con.commit()
con.close()
