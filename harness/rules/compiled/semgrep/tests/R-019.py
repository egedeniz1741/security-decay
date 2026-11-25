import os
from flask import request, send_file
from werkzeug.utils import secure_filename

UPLOAD_DIR = "/srv/uploads"


def bad_join():
    name = request.args.get("name")
    # ruleid: R-019
    path = os.path.join(UPLOAD_DIR, name)
    return path


def bad_save():
    f = request.files["file"]
    # ruleid: R-019
    f.save(os.path.join(UPLOAD_DIR, f.filename))


def bad_open():
    name = request.form["name"]
    # ruleid: R-019
    return open(name).read()


def bad_send_file():
    name = request.args.get("f")
    # ruleid: R-019
    return send_file(name)


def bad_filename_join():
    # ruleid: R-019
    return os.path.join(UPLOAD_DIR, request.files["file"].filename)


def good_save():
    f = request.files["file"]
    name = secure_filename(f.filename)
    # ok: R-019
    f.save(os.path.join(UPLOAD_DIR, name))


def good_open():
    name = secure_filename(request.args.get("name", ""))
    # ok: R-019
    return open(os.path.join(UPLOAD_DIR, name)).read()


def good_constant():
    # ok: R-019
    return open("config.txt").read()


def good_constant_join():
    # ok: R-019
    return os.path.join(UPLOAD_DIR, "report.csv")
