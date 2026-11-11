# Examples for R-002 (SQL queries must be parameterized).
# "ruleid" lines must be reported, "ok" lines must not.


def bad_fstring_inline(db, email):
    # ruleid: R-002
    return db.execute(f"SELECT * FROM users WHERE email = '{email}'").fetchone()


def bad_fstring_variable(db, username):
    query = f"SELECT * FROM users WHERE username = '{username}'"
    # ruleid: R-002
    return db.execute(query).fetchone()


def bad_percent(db, user_id):
    # ruleid: R-002
    return db.execute("SELECT * FROM orders WHERE user_id = %s" % user_id).fetchall()


def bad_format(db, name):
    # ruleid: R-002
    return db.execute("SELECT * FROM items WHERE name = '{}'".format(name)).fetchall()


def bad_concat(db, name):
    # ruleid: R-002
    return db.execute("SELECT * FROM items WHERE name = '" + name + "'").fetchall()


def ok_parameterized(db, email):
    # ok: R-002
    return db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()


def ok_named_parameter(db, username):
    query = "SELECT * FROM users WHERE username = :name"
    # ok: R-002
    return db.execute(query, {"name": username}).fetchone()


def ok_constant(db):
    # ok: R-002
    return db.execute("SELECT COUNT(*) FROM users").fetchone()
