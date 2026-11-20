import socket
import threading

import pytest
from conftest import NetworkBlocked


def test_guard_blocks_remote_host():
    """Broken case: without the guard this connect would reach out (or hang) instead of raising."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with pytest.raises(NetworkBlocked):
            s.connect(("93.184.216.34", 80))
    finally:
        s.close()


def test_guard_allows_loopback():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]
    t = threading.Thread(target=lambda: server.accept()[0].close())
    t.start()
    c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    c.connect(("127.0.0.1", port))
    c.close()
    t.join(timeout=5)
    server.close()
