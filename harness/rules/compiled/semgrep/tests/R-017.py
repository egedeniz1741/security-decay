import jwt

SECRET = "x"


def bad_no_algorithms(token):
    # ruleid: R-017
    return jwt.decode(token, SECRET)


def bad_verify_off(token):
    # ruleid: R-017
    return jwt.decode(token, options={"verify_signature": False})


def bad_verify_off_with_alg(token):
    # ruleid: R-017
    return jwt.decode(token, SECRET, algorithms=["HS256"], options={"verify_signature": False})


def bad_key_only_kw(token):
    # ruleid: R-017
    return jwt.decode(token, key=SECRET)


def good_pinned(token):
    # ok: R-017
    return jwt.decode(token, SECRET, algorithms=["HS256"])


def good_pinned_with_options(token):
    # ok: R-017
    return jwt.decode(token, SECRET, algorithms=["HS256"], options={"require": ["exp"]})


def good_encode(payload):
    # ok: R-017
    return jwt.encode(payload, SECRET, algorithm="HS256")


def good_other_decode(data):
    # ok: R-017
    return data.decode("utf-8")
