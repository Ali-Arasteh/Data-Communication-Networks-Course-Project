import socket
import json
import numpy
import time
from Message import Message


class MME:
    def __init__(self, Host):
        self.Host = Host
        self.ToSGWSocket = None
        self.ServerSocketForENodeBs = None
        self.ToENodeBsSockets = []
        self.UsersToENodeBsDistance = numpy.array([])
        self.ClosestENodeBsToUsers = []

    def connect_to_SGW(self, SGW):
        self.ToSGWSocket = socket.socket()
        self.ToSGWSocket.connect((SGW.Host, 45000))

    def new_connection_from_eNodeBs(self):
        if not self.ServerSocketForENodeBs:
            self.ServerSocketForENodeBs = socket.socket()
            self.ServerSocketForENodeBs.bind((self.Host, 46000))
        self.ServerSocketForENodeBs.listen()
        clientSocket, address = self.ServerSocketForENodeBs.accept()
        flag = 1
        ENodeBID = None
        while flag:
            data = clientSocket.recv(1024)
            if not data:
                flag = 0
                break
            receivedMessage = Message(**json.loads(data))
            if receivedMessage.messageType == 'eNodeB-MME connection':
                ENodeBID = receivedMessage.messageValue
                break
        while flag:
            data = clientSocket.recv(1024)
            if not data:
                break
            receivedMessage = Message(**json.loads(data))
            if receivedMessage.messageType == 'User distance':
                UserID = receivedMessage.messageValue[0]
                Distance = receivedMessage.messageValue[1]
                self.UsersToENodeBsDistance[UserID, ENodeBID] = Distance
                time.sleep(0.25)
                if self.ClosestENodeBsToUsers[UserID] != self.UsersToENodeBsDistance[UserID, :].tolist().index(min(self.UsersToENodeBsDistance[UserID, :])):
                    if self.UsersToENodeBsDistance[UserID, :].tolist().index(min(self.UsersToENodeBsDistance[UserID, :])) == ENodeBID:
                        sendMessage = Message('User Registration1', (UserID, self.ClosestENodeBsToUsers[UserID]))
                        self.ToENodeBsSockets[ENodeBID].send(json.dumps(sendMessage.__dict__).encode("utf-8"))
                        sendMessage = Message('Change Route', (UserID, ENodeBID))
                        self.ToSGWSocket.send(json.dumps(sendMessage.__dict__).encode("utf-8"))
                        self.ClosestENodeBsToUsers[UserID] = self.UsersToENodeBsDistance[UserID, :].tolist().index(min(self.UsersToENodeBsDistance[UserID, :]))

        self.ServerSocketForENodeBs.close()

    def connect_to_ENodeBs(self, ENodeB):
        ToENodeBsSocket = socket.socket()
        ToENodeBsSocket.connect((ENodeB.ENodeBHost, 48000))
        self.ToENodeBsSockets.append(ToENodeBsSocket)
