"""Safe socket handling with explicit close."""

import socket

def fetch_data():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("example.com", 80))
    sock.send(b"GET / HTTP/1.0\r\n\r\n")
    data = sock.recv(1024)
    sock.close()  # Safe: explicitly closed
    return data
