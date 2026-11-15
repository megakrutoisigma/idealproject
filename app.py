import os
import platform
import sys
import time
from datetime import datetime

import psutil
from flask import Flask, make_response, render_template

app = Flask(__name__)


def to_gb(size):
    return f"{size / (1024 ** 3):.2f}"


def get_system_info():
    # Учитываем 64-битную Windows даже при запуске 32-битного Python.
    machine = (os.environ.get("PROCESSOR_ARCHITEW6432") or platform.machine()).lower()
    architecture = "Неизвестно"
    if machine in ("amd64", "x86_64", "arm64", "aarch64"):
        architecture = "64 бита"
    elif machine in ("x86", "i386", "i686", "arm", "armv7l"):
        architecture = "32 бита"
    return {
        "name": f"{platform.system()} {platform.release()}".strip() or "Неизвестно",
        "version": platform.version() or "Неизвестно",
        "architecture": architecture,
        "hostname": platform.node() or os.environ.get("COMPUTERNAME") or "Неизвестно",
    }


def get_cpu_info():
    try:
        name = platform.processor()
    except OSError:
        name = None
    try:
        cores = psutil.cpu_count(logical=False)
    except (OSError, NotImplementedError, psutil.Error):
        cores = None
    try:
        # Небольшой интервал даёт настоящий замер уже при первом открытии.
        percent = psutil.cpu_percent(interval=0.2)
    except (OSError, NotImplementedError, psutil.Error):
        percent = None
    return {
        "name": name or os.environ.get("PROCESSOR_IDENTIFIER") or "Неизвестно",
        "cores": cores or "Недоступно",
        "threads": os.cpu_count() or "Недоступно",
        "percent": percent,
    }


def get_memory_info():
    try:
        memory = psutil.virtual_memory()
    except (OSError, NotImplementedError, psutil.Error):
        return None
    return {
        "total": to_gb(memory.total),
        "used": to_gb(memory.used),
        "available": to_gb(memory.available),
        "percent": memory.percent,
    }


def get_disk_info():
    # SystemDrive указывает диск Windows, независимо от папки проекта.
    path = os.environ.get("SystemDrive", "C:") + "\\" if os.name == "nt" else "/"
    try:
        disk = psutil.disk_usage(path)
    except (OSError, NotImplementedError, psutil.Error):
        return None
    return {
        "path": path,
        "total": to_gb(disk.total),
        "used": to_gb(disk.used),
        "free": to_gb(disk.free),
        "percent": disk.percent,
    }


def get_uptime():
    try:
        seconds = max(0, int(time.time() - psutil.boot_time()))
    except (OSError, NotImplementedError, psutil.Error):
        return "Недоступно"
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes = seconds // 60
    return f"{days} д {hours} ч {minutes} мин"


@app.route("/")
def index():
    response = make_response(render_template(
        "index.html",
        system=get_system_info(),
        cpu=get_cpu_info(),
        memory=get_memory_info(),
        disk=get_disk_info(),
        uptime=get_uptime(),
        python_version=sys.version.split()[0],
        python_platform=sys.platform,
        updated_at=datetime.now().strftime("%d.%m.%Y · %H:%M:%S"),
    ))
    # При обновлении браузер должен получить свежие показатели.
    response.headers["Cache-Control"] = "no-store"
    return response


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
