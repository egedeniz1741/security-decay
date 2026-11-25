from flask import Flask

app = Flask(__name__)


def bad_run():
    # ruleid: R-014
    app.run(debug=True)


def bad_run_host():
    # ruleid: R-014
    app.run(host="0.0.0.0", port=5000, debug=True)


def bad_attr():
    # ruleid: R-014
    app.debug = True


def bad_config():
    # ruleid: R-014
    app.config["DEBUG"] = True


def good_run():
    # ok: R-014
    app.run(debug=False)


def good_run_plain():
    # ok: R-014
    app.run(host="127.0.0.1", port=5000)


def good_attr():
    # ok: R-014
    app.debug = False


def good_lookalike():
    debug = True
    # ok: R-014
    print(debug)
