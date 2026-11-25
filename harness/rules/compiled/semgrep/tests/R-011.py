import pickle
import json
import yaml
from flask import Flask, request

app = Flask(__name__)


@app.route("/a")
def bad_eval():
    expr = request.args.get("e")
    # ruleid: R-011
    return str(eval(expr))


@app.route("/b")
def bad_exec():
    # ruleid: R-011
    exec(request.form["code"])
    return "ok"


@app.route("/c")
def bad_pickle():
    blob = request.get_data()
    # ruleid: R-011
    obj = pickle.loads(blob)
    return str(obj)


@app.route("/d")
def bad_yaml():
    body = request.data
    # ruleid: R-011
    cfg = yaml.load(body, Loader=yaml.Loader)
    return str(cfg)


@app.route("/e")
def bad_yaml_default():
    # ruleid: R-011
    cfg = yaml.load(request.data)
    return str(cfg)


@app.route("/f")
def good_json():
    ok_data = json.loads(request.data)
    return str(ok_data)


@app.route("/g")
def good_safe_load():
    # ok: R-011
    cfg = yaml.safe_load(request.data)
    return str(cfg)


@app.route("/h")
def good_constants():
    # ok: R-011
    v = eval("1 + 2")
    # ok: R-011
    w = pickle.loads(b"\x80\x04N.")
    return str(v) + str(w)


@app.route("/i")
def good_safe_loader():
    # ok: R-011
    cfg = yaml.load(request.data, Loader=yaml.SafeLoader)
    return str(cfg)


def good_local_file():
    with open("conf.yml") as fh:
        # ok: R-011
        return yaml.load(fh.read(), Loader=yaml.Loader)
