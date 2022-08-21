import socket
import json

class Message:
    def __init__(self, type, value):
        self.type = type
        self.value = value

host = '127.0.0.1'
port = 52012

server_socket = socket.socket()
server_socket.bind((host, port))
server_socket.listen(2)

conn, address = server_socket.accept()


while True:
    data = conn.recv(1024)
    if not data:
       break

    msg_rec = Message(**json.loads(data, encoding="utf-8"))
    print(msg_rec.type, msg_rec.value)

    if msg_rec.type == 'start':
        msg_snd = Message('start', 'hi')
        byte_array = json.dumps(msg_snd.__dict__).encode("utf-8")
        conn.send(byte_array)

    elif msg_rec.type == 'end':
        msg_snd = Message('end', 'bye')
        byte_array = json.dumps(msg_snd.__dict__).encode("utf-8")
        conn.send(byte_array)
        break
