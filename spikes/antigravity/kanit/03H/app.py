import sqlite3


def get_db():
    conn = sqlite3.connect("app.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    db = get_db()
    db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, email TEXT)")
    db.commit()


def get_user_by_email(email):
    db = get_db()
    query = "SELECT * FROM users WHERE email = ?"
    return db.execute(query, (email,)).fetchone()

