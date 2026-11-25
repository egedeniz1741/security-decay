import subprocess


def bad_run(cmd):
    # ruleid: R-018
    subprocess.run(cmd, shell=True)


def bad_popen(name):
    # ruleid: R-018
    return subprocess.Popen("ls " + name, shell=True, stdout=subprocess.PIPE)


def bad_check_output(name):
    # ruleid: R-018
    return subprocess.check_output(f"cat {name}", shell=True)


def bad_call():
    # ruleid: R-018
    subprocess.call("echo hi", shell=True)


def good_list(name):
    # ok: R-018
    subprocess.run(["ls", name], check=True)


def good_explicit_false(name):
    # ok: R-018
    subprocess.run(["ls", name], shell=False)


def good_popen(name):
    # ok: R-018
    return subprocess.Popen(["cat", name])
