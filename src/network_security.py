import socket
import sys
import contextlib

# Store originals at module level
_original_socket = socket.socket
_original_create_connection = socket.create_connection
_original_getaddrinfo = socket.getaddrinfo

# Define blocked implementations
def blocked_create_connection(address, *args, **kwargs):
    host, port = address
    raise RuntimeError(f"Network connection to {host}:{port} blocked by Security Policy.")

def blocked_getaddrinfo(host, port, *args, **kwargs):
    # Allow localhost resolution
    if host in ['localhost', '127.0.0.1', '::1']:
            return _original_getaddrinfo(host, port, *args, **kwargs)
    raise RuntimeError(f"DNS lookup for {host} blocked by Security Policy.")

class SecureSocket(_original_socket):
    def connect(self, address):
        host = address[0] if isinstance(address, tuple) else address
        raise RuntimeError(f"Network connection to {host} blocked by Security Policy.")
        
    def connect_ex(self, address):
        host = address[0] if isinstance(address, tuple) else address
        raise RuntimeError(f"Network connection to {host} blocked by Security Policy.")

def install_network_lock():
    """
    Installs a hard-coded block on outbound network calls by patching the socket module.
    This ensures the application operates in a Local-Only mode.
    """
    disable_network()
    print("Security: Network Lock installed. Outbound traffic is blocked.")

def disable_network():
    """Patches socket module to block connections."""
    socket.create_connection = blocked_create_connection
    socket.getaddrinfo = blocked_getaddrinfo
    socket.socket = SecureSocket

def enable_network():
    """Restores original socket module functions (CAUTION: Enables Internet Access)."""
    socket.create_connection = _original_create_connection
    socket.getaddrinfo = _original_getaddrinfo
    socket.socket = _original_socket

@contextlib.contextmanager
def temporarily_allow_network():
    """
    Context manager to safely temporarily enable network access.
    Usage:
        with temporarily_allow_network():
            # do network stuff
    """
    enable_network()
    try:
        yield
    finally:
        disable_network()

