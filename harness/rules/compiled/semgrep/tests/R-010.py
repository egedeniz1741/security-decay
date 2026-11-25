import sqlite3


def bad_fstring(db, name):
    cur = db.cursor()
    # ruleid: R-010
    cur.execute(f"SELECT * FROM users WHERE name = '{name}'")


def bad_percent(db, name):
    # ruleid: R-010
    db.execute("SELECT * FROM users WHERE name = '%s'" % name)


def bad_concat(db, name):
    # ruleid: R-010
    db.execute("SELECT * FROM users WHERE name = '" + name + "'")


def bad_format(db, name):
    # ruleid: R-010
    db.execute("SELECT * FROM users WHERE name = '{}'".format(name))


def good_param(db, name):
    # ok: R-010
    db.execute("SELECT * FROM users WHERE name = ?", (name,))


def good_constant(db):
    # ok: R-010
    db.execute("SELECT * FROM users " + "WHERE active = 1")


def good_in_list(db, ids):
    placeholders = ",".join("?" * len(ids))
    # ok: R-010
    db.execute(f"SELECT * FROM users WHERE id IN ({placeholders})", ids)


def good_plain(db):
    # ok: R-010
    db.execute("SELECT 1")
