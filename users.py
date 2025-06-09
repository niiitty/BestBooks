import db
from werkzeug.security import generate_password_hash, check_password_hash

def create_user(username, password):
    password_hash = generate_password_hash(password)
    sql = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
    db.execute(sql, [username, password_hash])

def check_login(username, password):
    sql = "SELECT password_hash, user_id FROM users WHERE username = ?"
    result = db.query(sql, [username])

    if not result:
        return None
    
    if check_password_hash(result[0]["password_hash"], password):
        return result[0]["user_id"]
    return None
