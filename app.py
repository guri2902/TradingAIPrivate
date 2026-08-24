import socket
import sys
import threading
import time

import uvicorn
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


API_HOST = "127.0.0.1"
API_PORT = 8000


def start_api_server():
    """
    Start FastAPI/Uvicorn in a background daemon thread so the
    desktop Qt application and API share the same Python process.
    """

    config = uvicorn.Config(
        "api.tradingai_api:app",
        host=API_HOST,
        port=API_PORT,
        log_level="info",
    )

    server = uvicorn.Server(config)

    thread = threading.Thread(
        target=server.run,
        name="TradingAI-API",
        daemon=True,
    )

    thread.start()

    return server, thread


def wait_for_api(
    host=API_HOST,
    port=API_PORT,
    timeout=15,
):
    """
    Wait until FastAPI is actually listening before starting the
    desktop UI. This prevents the MarketWorker from getting
    connection-refused errors during startup.
    """

    deadline = time.time() + timeout

    while time.time() < deadline:

        try:

            with socket.create_connection(
                (host, port),
                timeout=0.5,
            ):
                return True

        except OSError:
            time.sleep(0.25)

    return False


def main():

    print("=" * 70)
    print("TradingAI")
    print("=" * 70)

    # ------------------------------------------------------------
    # START API
    # ------------------------------------------------------------

    print(
        f"[APP] Starting TradingAI API "
        f"on http://{API_HOST}:{API_PORT}"
    )

    api_server, api_thread = (
        start_api_server()
    )

    if wait_for_api():

        print(
            f"[APP] API ready: "
            f"http://{API_HOST}:{API_PORT}"
        )

    else:

        print(
            "[APP] WARNING: API did not become ready "
            "within the startup timeout."
        )

    # ------------------------------------------------------------
    # START DESKTOP APP
    # ------------------------------------------------------------

    qt_app = QApplication(
        sys.argv
    )

    window = MainWindow()

    window.showMaximized()

    # ------------------------------------------------------------
    # SHUTDOWN
    # ------------------------------------------------------------

    def shutdown_api():

        print(
            "[APP] Shutting down TradingAI API..."
        )

        api_server.should_exit = True

        if api_thread.is_alive():

            api_thread.join(
                timeout=5
            )

    qt_app.aboutToQuit.connect(
        shutdown_api
    )

    print(
        "[APP] TradingAI desktop application started."
    )

    return qt_app.exec()


if __name__ == "__main__":
    sys.exit(
        main()
    )