import ast
import json


def bad_eval(value):
    # ruleid: R-002
    return eval(value)


def bad_exec(code):
    # ruleid: R-002
    exec(code)


def bad_eval_globals(value):
    # ruleid: R-002
    return eval(value, {})


def good_literal(value):
    # ok: R-002
    return ast.literal_eval(value)


def good_json(value):
    # ok: R-002
    return json.loads(value)


def good_method(obj):
    # ok: R-002
    return obj.evaluate()
