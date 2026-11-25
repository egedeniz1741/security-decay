import os
import jwt
from flask import Flask

app = Flask(__name__)

PASSWORD_MIN_LENGTH = 12


def bad_assign():
    # ruleid: R-013
    SECRET_KEY = "hunter2-super-secret"
    return SECRET_KEY


def bad_password():
    # ruleid: R-013
    db_password = "p@ssw0rd"
    return db_password


def bad_config():
    # ruleid: R-013
    app.config["SECRET_KEY"] = "dev-key-123"


def bad_jwt_encode(payload):
    # ruleid: R-013
    return jwt.encode(payload, "my-jwt-secret", algorithm="HS256")


def bad_jwt_decode(token):
    # ruleid: R-013
    return jwt.decode(token, "my-jwt-secret", algorithms=["HS256"])


def good_env():
    # ok: R-013
    SECRET_KEY = os.environ["SECRET_KEY"]
    return SECRET_KEY


def good_env_default_empty():
    # ok: R-013
    api_key = os.environ.get("API_KEY", "")
    return api_key


def good_config():
    # ok: R-013
    app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]


def good_jwt(payload):
    # ok: R-013
    return jwt.encode(payload, os.environ["JWT_SECRET"], algorithm="HS256")


def good_constant():
    # ok: R-013
    label = "password"
    return label
