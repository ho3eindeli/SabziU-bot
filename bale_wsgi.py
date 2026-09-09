import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PID_FILE = os.path.join(BASE_DIR, ".bale_bot.pid")
LOG_FILE = os.path.join(BASE_DIR, "bale_bot.log")


def _running(pid):
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def start_bot():
    try:
        if os.path.exists(PID_FILE):
            with open(PID_FILE, "r", encoding="utf-8") as f:
                pid = int(f.read().strip())
            if _running(pid):
                return pid
            os.remove(PID_FILE)
    except (ValueError, OSError):
        try:
            os.remove(PID_FILE)
        except OSError:
            pass

    log = open(LOG_FILE, "a", encoding="utf-8", buffering=1)
    process = subprocess.Popen(
        [sys.executable, os.path.join(BASE_DIR, "bale_bot.py")],
        cwd=BASE_DIR,
        stdin=subprocess.DEVNULL,
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )

    with open(PID_FILE, "w", encoding="utf-8") as f:
        f.write(str(process.pid))

    return process.pid


start_bot()


def application(environ, start_response):
    body = b"SabziU Bale bot is running."
    start_response(
        "200 OK",
        [
            ("Content-Type", "text/plain; charset=utf-8"),
            ("Content-Length", str(len(body))),
        ],
    )
    return [body]
