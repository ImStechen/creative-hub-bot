import os
import subprocess
import sys

BOT_CMDLINE_MARKERS = ("main.py",)


def _parse_wmic_python_processes(output: str) -> list[tuple[int, str]]:
    processes = []
    for line in output.splitlines():
        line = line.strip()
        if not line or line.lower().startswith("commandline") or "processid" in line.lower() and "commandline" in line.lower():
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        try:
            pid = int(parts[-1])
        except ValueError:
            continue
        cmdline = " ".join(parts[:-1]).lower()
        processes.append((pid, cmdline))
    return processes


def list_python_processes() -> list[tuple[int, str]]:
    if os.name == "nt":
        processes = []
        for exe_name in ("python.exe", "pythonw.exe"):
            try:
                output = subprocess.check_output(
                    ["wmic", "process", "where", f"name='{exe_name}'", "get", "commandline,processid"],
                    text=True,
                    errors="ignore",
                    timeout=15,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                processes.extend(_parse_wmic_python_processes(output))
            except (subprocess.SubprocessError, FileNotFoundError, OSError):
                continue
        return processes

    try:
        output = subprocess.check_output(
            ["ps", "-eo", "pid,args"],
            text=True,
            errors="ignore",
            timeout=15,
        )
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return []

    processes = []
    for line in output.splitlines()[1:]:
        line = line.strip()
        if not line:
            continue
        pid_str, _, rest = line.partition(" ")
        try:
            pid = int(pid_str)
        except ValueError:
            continue
        processes.append((pid, rest.lower()))
    return processes


def _is_bot_process(cmdline: str) -> bool:
    return any(marker in cmdline for marker in BOT_CMDLINE_MARKERS)


def kill_other_bot_processes(exclude_pid: int | None = None) -> int:
    """
    Завершает другие процессы бота (main.py). Без shell=True.
    Возвращает число успешно посланных сигналов/taskkill.
    """
    current = os.getpid() if exclude_pid is None else exclude_pid
    killed = 0
    for pid, cmdline in list_python_processes():
        if pid in (current, os.getpid()):
            continue
        if not _is_bot_process(cmdline):
            continue
        try:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/F", "/PID", str(pid)],
                    check=False,
                    timeout=10,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
            else:
                os.kill(pid, 15)
            killed += 1
        except (OSError, subprocess.SubprocessError):
            continue
    return killed


def start_bot_detached() -> None:
    creationflags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0) if os.name == "nt" else 0
    subprocess.Popen([sys.executable, "main.py"], creationflags=creationflags)
