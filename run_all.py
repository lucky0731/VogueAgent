"""
Run the store and the shopping assistant together.

    python run_all.py

- starts the store (default port 8000) and the chatbot (default port 8001),
  each with its own virtual environment
- points the chatbot's product links at the store's actual port
- shows both logs in this window, prefixed [store] / [chat]
- opens both in the browser once they're up
- Ctrl+C stops both

Environments are found automatically (store: fashionagent/, .venv/ or venv/;
chatbot: chatbot/webchatbot/, chatbot/.venv/ or chatbot/venv/). Override with
STORE_PYTHON / CHATBOT_PYTHON if yours live elsewhere.
"""
import os
import signal
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CHATBOT_DIR = ROOT / "chatbot"
IS_WINDOWS = os.name == "nt"


def find_python(folder: Path, env_names: list[str], override_var: str) -> str:
    """The Python inside the first virtual environment found in `folder`."""
    if os.environ.get(override_var):
        return os.environ[override_var]
    for name in env_names:
        exe = folder / name / ("Scripts/python.exe" if IS_WINDOWS else "bin/python")
        if exe.exists():
            return str(exe)
    sys.exit(
        f"Couldn't find a virtual environment in {folder} (looked for {', '.join(env_names)}).\n"
        f"Create one and install requirements.txt there, or set {override_var} to its python."
    )


def free_port(start: int, avoid: set[int] = frozenset()) -> int:
    port = start
    while port in avoid or not _is_free(port):
        port += 1
    return port


def _is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


def wait_until_up(port: int, proc: subprocess.Popen, timeout: float = 90) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            return False
        if not _is_free(port):
            return True
        time.sleep(0.5)
    return False


def stream(proc: subprocess.Popen, label: str) -> None:
    for line in iter(proc.stdout.readline, ""):
        print(f"{label} {line}", end="", flush=True)


def start(label: str, python: str, cwd: Path, port: int, extra_env: dict) -> subprocess.Popen:
    env = {**os.environ, "PORT": str(port), "OPEN_BROWSER": "false", "PYTHONUNBUFFERED": "1",
           "PYTHONIOENCODING": "utf-8", **extra_env}
    kwargs = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if IS_WINDOWS else {"start_new_session": True}
    proc = subprocess.Popen(
        [python, "main.py"], cwd=cwd, env=env, text=True, encoding="utf-8", errors="replace",
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **kwargs,
    )
    threading.Thread(target=stream, args=(proc, label), daemon=True).start()
    return proc


def stop(procs: list[subprocess.Popen]) -> None:
    for p in procs:
        if p.poll() is None:
            try:
                p.send_signal(signal.CTRL_BREAK_EVENT if IS_WINDOWS else signal.SIGINT)
            except (OSError, ValueError):
                p.terminate()
    deadline = time.time() + 8
    for p in procs:
        try:
            p.wait(timeout=max(0.1, deadline - time.time()))
        except subprocess.TimeoutExpired:
            p.kill()


def main() -> None:
    store_python = find_python(ROOT, ["fashionagent", ".venv", "venv"], "STORE_PYTHON")
    chat_python = find_python(CHATBOT_DIR, ["webchatbot", ".venv", "venv"], "CHATBOT_PYTHON")

    store_port = free_port(int(os.environ.get("STORE_PORT", 8000)))
    chat_port = free_port(int(os.environ.get("CHATBOT_PORT", 8001)), avoid={store_port})
    store_url = f"http://localhost:{store_port}"
    chat_url = f"http://localhost:{chat_port}"

    print(f"Starting the store on {store_url} and the shopping assistant on {chat_url} ...")
    print("Press Ctrl+C to stop both.\n")

    store = start("[store]", store_python, ROOT, store_port, {})
    chat = start("[chat] ", chat_python, CHATBOT_DIR, chat_port, {"STORE_URL": store_url})
    procs = [store, chat]

    try:
        store_ok = wait_until_up(store_port, store)
        chat_ok = wait_until_up(chat_port, chat)
        if store_ok and chat_ok:
            print(f"\n  Store:     {store_url}\n  Assistant: {chat_url}\n", flush=True)
            webbrowser.open(store_url)
            webbrowser.open(chat_url)
        else:
            failed = "store" if not store_ok else "shopping assistant"
            print(f"\nThe {failed} didn't start — see its messages above. Stopping.", flush=True)
            stop(procs)
            sys.exit(1)

        # If either app stops on its own, stop the other too.
        while all(p.poll() is None for p in procs):
            time.sleep(0.5)
        which = "store" if store.poll() is not None else "shopping assistant"
        print(f"\nThe {which} stopped — shutting down the other one.", flush=True)
    except KeyboardInterrupt:
        print("\nStopping both apps ...", flush=True)
    finally:
        stop(procs)
        print("Stopped.")


if __name__ == "__main__":
    main()
