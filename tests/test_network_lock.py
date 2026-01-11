import pytest
import socket
import urllib.request
from src.network_security import install_network_lock

# Install lock manually for this test if not already installed by importing main
install_network_lock()

def test_socket_connect_blocked():
    """Test that direct socket connections are blocked."""
    with pytest.raises(RuntimeError, match="blocked by Security Policy"):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("8.8.8.8", 53))

def test_create_connection_blocked():
    """Test that socket.create_connection is blocked."""
    with pytest.raises(RuntimeError, match="blocked by Security Policy"):
        socket.create_connection(("google.com", 80))

def test_urllib_blocked():
    """Test that high-level libraries like urllib are blocked."""
    with pytest.raises(RuntimeError, match="blocked by Security Policy"):
        urllib.request.urlopen("http://example.com")
