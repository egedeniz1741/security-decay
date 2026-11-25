import hashlib
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash


def bad_plain_insert(db, username, password):
    # ruleid: R-015
    db.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))


def bad_plain_update(cur, pwd, uid):
    # ruleid: R-015
    cur.execute("UPDATE users SET password = ? WHERE id = ?", (pwd, uid))


def bad_unsalted_sha256(password):
    # ruleid: R-015
    return hashlib.sha256(password.encode()).hexdigest()


def bad_md5(password):
    # ruleid: R-015
    return hashlib.md5(password).hexdigest()


def good_hashed_insert(db, username, password):
    hashed = generate_password_hash(password)
    # ok: R-015
    db.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))


def good_reassigned(db, username, password):
    password = generate_password_hash(password)
    # ok: R-015
    db.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))


def good_other_column(db, name, email):
    # ok: R-015
    db.execute("INSERT INTO users (name, email) VALUES (?, ?)", (name, email))


def good_hash_of_file(data):
    # ok: R-015
    return hashlib.sha256(data).hexdigest()


PASSWORD_MIN_LENGTH = 12


def good_verify(stored, password):
    # ok: R-015
    return check_password_hash(stored, password)
