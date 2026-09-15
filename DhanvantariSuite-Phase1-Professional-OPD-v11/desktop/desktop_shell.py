import os
import sys
import socket
import threading
import time
import uvicorn
import webview

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)


def find_free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port


def run_local_backend(port: int):
    os.environ.setdefault("DATABASE_URL", "sqlite:///clinic_local.db")
    uvicorn.run("src.main:app", host="127.0.0.1", port=port, log_level="info")


def main():
    # Production/LAN mode: set ERP_SERVER_URL on every client PC, e.g.
    # http://192.168.1.20:8000 . The central server owns the database.
    server_url = os.environ.get("ERP_SERVER_URL", "").strip().rstrip("/")
    if server_url:
        url = server_url + "/ui/"
        print(f"Launching ERP client against central server: {url}")
    else:
        port = find_free_port()
        backend_thread = threading.Thread(target=run_local_backend, args=(port,), daemon=True)
        backend_thread.start()
        time.sleep(1)
        url = f"http://127.0.0.1:{port}/ui/"
        print(f"Launching single-PC local ERP: {url}")

    webview.create_window(
        title="Dhanvantari Clinic ERP",
        url=url,
        width=1360,
        height=850,
        min_size=(1100, 700),
        resizable=True,
    )
    webview.start()
    sys.exit(0)


if __name__ == "__main__":
    main()
