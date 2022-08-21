import socket
import json

class Message:
    def __init__(self, type, value):
        self.type = type
        self.value = value

host = '127.0.0.1'
port = 52012  

client_socket = socket.socket()  
client_socket.connect((host, port))  
msg_snd = Message('start', 'hello')
byte_array = json.dumps(msg_snd.__dict__).encode("utf-8")

while True:
    client_socket.send(byte_array)

    data = client_socket.recv(1024)
    msg_rec = Message(**json.loads(data, encoding="utf-8"))
    print(msg_rec.type, msg_rec.value)

    if msg_rec.type == 'end':
        break

    elif msg_rec.type == 'start':
        msg_snd = Message('end', 'goodbye')
        byte_array = json.dumps(msg_snd.__dict__).encode("utf-8")
        client_socket.send(byte_array)

client_socket.close()
