"""Multiple different resource leaks in one file."""

import socket
import sqlite3

def multi_resource_mess():
    # Leak 1: file
    f = open("data.txt", "r")
    content = f.read()
    
    # Leak 2: socket
    sock = socket.create_connection(("localhost", 8080))
    sock.send(b"hello")
    
    # Leak 3: database
    db = sqlite3.connect("app.db")
    cursor = db.cursor()
    cursor.execute("SELECT 1")
    
    return content  # All three resources leaked
