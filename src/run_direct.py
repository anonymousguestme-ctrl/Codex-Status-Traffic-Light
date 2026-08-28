"""Windows entry point: talk to a dedicated Codex app-server over stdio."""

import json
import queue
import subprocess
import sys
import threading

import codex_traffic_light as app


class WindowsJsonRpcClient(app.JsonRpcClient):
    def __init__(self, codex_executable: str) -> None:
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        self.process = subprocess.Popen(
            [codex_executable, "app-server", "--listen", "stdio://"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
            creationflags=creationflags,
        )
        self.responses: queue.Queue[dict] = queue.Queue()
        self.next_id = 1
        self.reader = threading.Thread(target=self._read_stdout, daemon=True)
        self.reader.start()


app.JsonRpcClient = WindowsJsonRpcClient

if __name__ == "__main__":
    raise SystemExit(app.main())
