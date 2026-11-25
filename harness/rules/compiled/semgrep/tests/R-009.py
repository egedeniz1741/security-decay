import sqlite3


def bad_fstring(conn, name):
    cur = conn.cursor()
    # ruleid: R-009
    cur.execute(f"SELECT * FROM users WHERE name = '{name}'")


def bad_percent(conn, name):
    # ruleid: R-009
    conn.execute("SELECT * FROM users WHERE name = '%s'" % name)


def bad_concat(conn, name):
    # ruleid: R-009
    conn.execute("SELECT * FROM users WHERE name = '" + name + "'")


def bad_format(conn, name):
    # ruleid: R-009
    conn.execute("SELECT * FROM users WHERE name = '{}'".format(name))


def bad_executemany(conn, rows, table):
    # ruleid: R-009
    conn.executemany(f"INSERT INTO {table} VALUES (?, ?)", rows)


def good_param(conn, name):
    # ok: R-009
    conn.execute("SELECT * FROM users WHERE name = ?", (name,))


def good_constant(conn):
    # ok: R-009
    conn.execute("SELECT * FROM users")


def good_in_list(conn, ids):
    placeholders = ",".join("?" * len(ids))
    # ok: R-009
    conn.execute(f"SELECT * FROM users WHERE id IN ({placeholders})", ids)


def good_constant_concat(conn):
    # ok: R-009
    conn.execute("SELECT * FROM users " + "WHERE id = 1")


def good_other_call(name):
    # ok: R-009
    print("hello %s" % name)
