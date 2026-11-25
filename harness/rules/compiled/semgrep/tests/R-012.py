import os
import jwt
from flask import Flask

app = Flask(__name__)

PASSWORD_MIN_LENGTH = 12
PASSWORD_FIELD = "password"


def bad_assign():
    # ruleid: R-012
    DB_PASSWORD = "hunter2-prod"
    return DB_PASSWORD


def bad_config():
    # ruleid: R-012
    app.config["SECRET_KEY"] = "dev-secret-123"


def bad_attr():
    # ruleid: R-012
    app.secret_key = "supersecret"


def bad_jwt_encode(payload):
    # ruleid: R-012
    return jwt.encode(payload, "my-jwt-secret", algorithm="HS256")


def bad_jwt_decode(tok):
    # ruleid: R-012
    return jwt.decode(tok, "my-jwt-secret", algorithms=["HS256"])


def bad_api_key():
    # ruleid: R-012
    api_key = "sk_live_abcdef"
    return api_key


def good_env():
    # ok: R-012
    secret_key = os.environ["SECRET_KEY"]
    return secret_key


def good_env_get():
    # ok: R-012
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")


def good_jwt(payload):
    key = os.environ["JWT_KEY"]
    # ok: R-012
    return jwt.encode(payload, key, algorithm="HS256")


def good_empty():
    # ok: R-012
    password = ""
    return password


def good_lookalike():
    # ok: R-012
    token_header = "X-Token"
    return token_header
