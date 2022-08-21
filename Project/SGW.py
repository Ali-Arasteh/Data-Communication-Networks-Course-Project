import socket
import json
import numpy
from Message import Message


class SGW:
    def __init__(self, Host):
        self.Host = Host
        self.ServerSocketForMME = None
        self.ServerSocketForENodeBs = None
        self.ToENodeBsSockets = []
        self.RoutingTable = []

    def new_connection_from_MME(self):
        self.ServerSocketForMME = socket.socket()
        self.ServerSocketForMME.bind((self.Host, 45000))
        self.ServerSocketForMME.listen()
        clientSocket, address = self.ServerSocketForMME.accept()
        while True:
            data = clientSocket.recv(1024)
            if not data:
                break
            receivedMessage = Message(**json.loads(data))
            if receivedMessage.messageType == 'Change Route':
                UserID = receivedMessage.messageValue[0]
                ENodeBID = receivedMessage.messageValue[1]
                self.RoutingTable[UserID] = ENodeBID
        self.ServerSocketForMME.close()

    def new_connection_from_eNodeBs(self):
        if not self.ServerSocketForENodeBs:
            self.ServerSocketForENodeBs = socket.socket()
            self.ServerSocketForENodeBs.bind((self.Host, 47000))
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
            if receivedMessage.messageType == 'eNodeB-SGW connection':
                ENodeBID = receivedMessage.messageValue
                break
        while flag:
            data = clientSocket.recv(1024)
            if not data:
                break
            receivedMessage = Message(**json.loads(data))
            if receivedMessage.messageType == 'User deregistration':
                PreviousENodeB = receivedMessage.messageValue[0]
                UserID = receivedMessage.messageValue[1]
                sendMessage = Message('User deregistration', UserID)
                self.ToENodeBsSockets[PreviousENodeB].send(json.dumps(sendMessage.__dict__).encode("utf-8"))
            elif receivedMessage.messageType == 'Send Me Buffered data':
                PreviousENodeB = receivedMessage.messageValue[0]
                NewENodeB = receivedMessage.messageValue[1]
                UserID = receivedMessage.messageValue[2]
                sendMessage = Message('Send Me Buffered data', (NewENodeB, UserID))
                self.ToENodeBsSockets[PreviousENodeB].send(json.dumps(sendMessage.__dict__).encode("utf-8"))
            elif receivedMessage.messageType == 'Buffered data':
                PreviousENodeB = receivedMessage.messageValue[0]
                UserID = receivedMessage.messageValue[1]
                BufferedData = receivedMessage.messageValue[2]
                sendMessage = Message('Buffered data', (UserID, BufferedData))
                self.ToENodeBsSockets[PreviousENodeB].send(json.dumps(sendMessage.__dict__).encode("utf-8"))
            elif receivedMessage.messageType == 'Handover complete':
                NewENodeB = receivedMessage.messageValue[0]
                UserID = receivedMessage.messageValue[1]
                sendMessage = Message('Handover complete', UserID)
                self.ToENodeBsSockets[NewENodeB].send(json.dumps(sendMessage.__dict__).encode("utf-8"))
            elif receivedMessage.messageType == 'Create Session':
                SenderID = receivedMessage.messageValue[0]
                ReceiverID = receivedMessage.messageValue[1]
                if self.RoutingTable[ReceiverID] != -1:
                    sendMessage = Message('Create Session', (SenderID, ReceiverID))
                    self.ToENodeBsSockets[self.RoutingTable[ReceiverID]].send(json.dumps(sendMessage.__dict__).encode("utf-8"))
            elif receivedMessage.messageType == 'Create Session Ack':
                SenderID = receivedMessage.messageValue[0]
                ReceiverID = receivedMessage.messageValue[1]
                if self.RoutingTable[ReceiverID] != -1:
                    sendMessage = Message('Create Session Ack', (SenderID, ReceiverID))
                    self.ToENodeBsSockets[self.RoutingTable[SenderID]].send(json.dumps(sendMessage.__dict__).encode("utf-8"))
            elif receivedMessage.messageType == 'Data Carrier':
                ReceiverID = receivedMessage.messageValue[0]
                Data = receivedMessage.messageValue[1]
                SequenceNumber = receivedMessage.messageValue[2]
                if self.RoutingTable[ReceiverID] != -1:
                    sendMessage = Message('Data Carrier', (ReceiverID, Data, SequenceNumber))
                    self.ToENodeBsSockets[self.RoutingTable[ReceiverID]].send(json.dumps(sendMessage.__dict__).encode("utf-8"))
        self.ServerSocketForENodeBs.close()

    def connect_to_ENodeBs(self, ENodeB):
        ToENodeBsSocket = socket.socket()
        ToENodeBsSocket.connect((ENodeB.ENodeBHost, 49000))
        self.ToENodeBsSockets.append(ToENodeBsSocket)
