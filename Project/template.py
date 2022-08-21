import threading
import socket
import time
import json


class Message:
    def __init__(self, ...):

class eNodeB:
    def __init__(self, id,location,...):


class MME:
    def __init__(self, ...):


class SGW:
    def __init__(self, ...):

class user:
    def __init__(self, id, [[x1, y1], [x2, y2], …] ,...):

class Network:
    def __init__(self, id,path,...):


    def init_network(self):
        # build network topology

    def add_user(self, id, [[x1, y1], [x2, y2], …] ):


    def connection_request(self, sender_id, receiver_id, file_name,...)


if __name__ == "__main__":
    network = Network()
    network.init_network(...)
    network.add_user(id, [[x1, y1], [x2, y2], …] )
    network.add_user(id, [[x1, y1], [x2, y2], …] )
    network.add_user(id, [[x1, y1], [x2, y2], …] )
    network.connection_request(sender_id, receiver_id, file_name,...)
