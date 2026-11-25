import jwt
from flask import request

SECRET = "x"


def bad_verify_false():
    token = request.headers.get("Authorization")
    # ruleid: R-016
    return jwt.decode(token, SECRET, verify=False)


def bad_options():
    token = request.headers.get("Authorization")
    # ruleid: R-016
    return jwt.decode(token, options={"verify_signature": False})


def bad_options_with_alg():
    token = request.headers.get("Authorization")
    # ruleid: R-016
    return jwt.decode(token, SECRET, algorithms=["HS256"], options={"verify_signature": False})


def bad_none_alg():
    token = request.headers.get("Authorization")
    # ruleid: R-016
    return jwt.decode(token, SECRET, algorithms=["none"])


def bad_no_algorithms():
    token = request.headers.get("Authorization")
    # ruleid: R-016
    return jwt.decode(token, SECRET)


def good_pinned():
    token = request.headers.get("Authorization")
    # ok: R-016
    return jwt.decode(token, SECRET, algorithms=["HS256"])


def good_options_other():
    token = request.headers.get("Authorization")
    # ok: R-016
    return jwt.decode(token, SECRET, algorithms=["HS256"], options={"verify_exp": True})


def good_encode():
    # ok: R-016
    return jwt.encode({"a": 1}, SECRET, algorithm="HS256")
