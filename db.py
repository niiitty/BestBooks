import sqlite3
from flask import g

def initialize_database(db_path="database.db"):
    with sqlite3.connect(db_path) as con:
        with open("schema.sql", "r", encoding="utf-8") as f:
            con.executescript(f.read())

def get_connection():
    con = sqlite3.connect("database.db")
    con.execute("PRAGMA foreign_keys = ON")
    con.row_factory = sqlite3.Row
    return con

def execute(sql, params=None):
    if not params:
        params = []
    con = get_connection()
    result = con.execute(sql, params)
    con.commit()
    g.last_insert_id = result.lastrowid
    con.close()

def last_insert_id():
    return g.last_insert_id

def query(sql, params=None):
    if not params:
        params = []
    con = get_connection()
    result = con.execute(sql, params).fetchall()
    con.close()
    return result
