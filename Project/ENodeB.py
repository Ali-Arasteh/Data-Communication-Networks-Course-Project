import socket
import json
import math
import numpy
import threading
from Message import Message


class ENodeB:
    def __init__(self, ENodeBID, ENodeBLocation):
        self.ENodeBID = ENodeBID
        self.ENodeBLocation = ENodeBLocation
        self.ENodeBHost = '127.0.1.' + str(self.ENodeBID)
        self.ToMMESocket = None
        self.ToSGWSocket = None
        self.ServerSocketForMME = None
        self.ServerSocketForSGW = None
        self.ServerSocketForUsersSignaling = None
        self.ToUsersSocketsForSignaling = []
        self.ServerSocketForUsersData = None
        self.SendToUsers = []
        self.UsersBufferedData = []
        self.SequenceNumbers = []
        self.ToUsersSocketsForData = ()

    def connect_to_MME(self, MME):
        self.ToMMESocket = socket.socket()
        self.ToMMESocket.connect((MME.Host, 46000))
        sendMessage = Message('eNodeB-MME connection', self.ENodeBID)
        self.ToMMESocket.send(json.dumps(sendMessage.__dict__).encode("utf-8"))
        
    def connect_to_SGW(self, SGW):
        self.ToSGWSocket = socket.socket()
        self.ToSGWSocket.connect((SGW.Host, 47000))
        sendMessage = Message('eNodeB-SGW connection', self.ENodeBID)
        self.ToSGWSocket.send(json.dumps(sendMessage.__dict__).encode("utf-8"))
        
    def new_connection_from_MME(self):
        self.ServerSocketForMME = socket.socket()
        self.ServerSocketForMME.bind((self.ENodeBHost, 48000))
        self.ServerSocketForMME.listen()
        clientSocket, address = self.ServerSocketForMME.accept()
        while True:
            data = clientSocket.recv(1024)
            if not data:
                break
            receivedMessage = Message(**json.loads(data))
            if receivedMessage.messageType == 'User Registration1':
                UserID = receivedMessage.messageValue[0]
                PreviousENodeB = receivedMessage.messageValue[1]
                if PreviousENodeB != -1:
                    sendMessage = Message('User deregistration', (PreviousENodeB, UserID))
                    self.ToSGWSocket.send(json.dumps(sendMessage.__dict__).encode("utf-8"))
                else:
                    self.SendToUsers[UserID] = 1
                threading.Thread(target=self.new_connection_from_Users_for_data, args=(PreviousENodeB, UserID, )).start()
                sendMessage = Message('User Registration2', (self.ENodeBHost, PreviousENodeB))
                self.ToUsersSocketsForSignaling[UserID].send(json.dumps(sendMessage.__dict__).encode("utf-8"))
        self.ServerSocketForMME.close()

    def new_connection_from_SGW(self):
        self.ServerSocketForSGW = socket.socket()
        self.ServerSocketForSGW.bind((self.ENodeBHost, 49000))
        self.ServerSocketForSGW.listen()
        clientSocket, address = self.ServerSocketForSGW.accept()
        while True:
            data = clientSocket.recv(1024)
            if not data:
                break
            receivedMessage = Message(**json.loads(data))
            if receivedMessage.messageType == 'User deregistration':
                UserID = receivedMessage.messageValue
                self.SendToUsers[UserID] = 0
            elif receivedMessage.messageType == 'Send Me Buffered data':
                NewENodeB = receivedMessage.messageValue[0]
                UserID = receivedMessage.messageValue[1]
                BufferedData = self.UsersBufferedData[UserID]
                SequenceNumber = self.SequenceNumbers[UserID]
                if BufferedData != '':
                    sendMessage = Message('Buffered data', (NewENodeB, UserID, BufferedData, SequenceNumber))
                    self.ServerSocketForSGW.send(json.dumps(sendMessage.__dict__).encode("utf-8"))
                    self.UsersBufferedData[UserID] = ''
                    self.SequenceNumbers[UserID] = -1
                sendMessage = Message('Handover complete', (NewENodeB, UserID))
                self.ToSGWSocket.send(json.dumps(sendMessage.__dict__).encode("utf-8"))
            elif receivedMessage.messageType == 'Buffered data':
                UserID = receivedMessage.messageValue[0]
                BufferedData = receivedMessage.messageValue[1]
                SequenceNumber = receivedMessage.messageValue[2]
                if SequenceNumber < self.SequenceNumbers[UserID]:
                    self.UsersBufferedData[UserID] = BufferedData + '\n' + self.UsersBufferedData[UserID]
                else:
                    self.UsersBufferedData[UserID] = self.UsersBufferedData[UserID] + '\n' + BufferedData
                    self.SequenceNumbers[UserID] = SequenceNumber
            elif receivedMessage.messageType == 'Handover complete':
                UserID = receivedMessage.messageValue
                self.SendToUsers[UserID] = 1
                if self.UsersBufferedData[UserID] != '':
                    sendMessage = Message('Data Carrier', self.UsersBufferedData[UserID])
                    for i in range(len(self.ToUsersSocketsForData)):
                        if self.ToUsersSocketsForData[i][0] == UserID:
                            self.ToUsersSocketsForData[i][1].send(json.dumps(sendMessage.__dict__).encode("utf-8"))
                            break
            elif receivedMessage.messageType == 'Create Session':
                SenderID = receivedMessage.messageValue[0]
                ReceiverID = receivedMessage.messageValue[1]
                if self.SendToUsers[ReceiverID]:
                    sendMessage = Message('Create Session', (SenderID, ReceiverID))
                    for i in range(len(self.ToUsersSocketsForData)):
                        if self.ToUsersSocketsForData[i][0] == ReceiverID:
                            self.ToUsersSocketsForData[i][1].send(json.dumps(sendMessage.__dict__).encode("utf-8"))
                            break
            elif receivedMessage.messageType == 'Create Session Ack':
                SenderID = receivedMessage.messageValue[0]
                ReceiverID = receivedMessage.messageValue[1]
                if self.SendToUsers[SenderID]:
                    sendMessage = Message('Create Session Ack', (SenderID, ReceiverID))
                    for i in range(len(self.ToUsersSocketsForData)):
                        if self.ToUsersSocketsForData[i][0] == SenderID:
                            self.ToUsersSocketsForData[i][1].send(json.dumps(sendMessage.__dict__).encode("utf-8"))
                            break
            elif receivedMessage.messageType == 'Data Carrier':
                ReceiverID = receivedMessage.messageValue[0]
                Data = receivedMessage.messageValue[1]
                SequenceNumber = receivedMessage.messageValue[2]
                if self.SendToUsers[ReceiverID]:
                    sendMessage = Message('Data Carrier', Data)
                    for i in range(len(self.ToUsersSocketsForData)):
                        if self.ToUsersSocketsForData[i][0] == ReceiverID:
                            self.ToUsersSocketsForData[i][1].send(json.dumps(sendMessage.__dict__).encode("utf-8"))
                            break
                else:
                    if SequenceNumber < self.SequenceNumbers[ReceiverID]:
                        self.UsersBufferedData = Data + self.UsersBufferedData
                    else:
                        self.UsersBufferedData = self.UsersBufferedData + Data
                        self.SequenceNumbers[ReceiverID] = SequenceNumber
        self.ServerSocketForSGW.close()

    def new_connection_from_Users_for_signaling(self):
        if not self.ServerSocketForUsersSignaling:
            self.ServerSocketForUsersSignaling = socket.socket()
            self.ServerSocketForUsersSignaling.bind((self.ENodeBHost, 50000))
        self.ServerSocketForUsersSignaling.listen()
        clientSocket, address = self.ServerSocketForUsersSignaling.accept()
        flag = 1
        UserID = None
        while flag:
            data = clientSocket.recv(1024)
            if not data:
                flag = 0
                break
            receivedMessage = Message(**json.loads(data))
            if receivedMessage.messageType == 'Signaling channel setup':
                UserID = receivedMessage.messageValue
                break
        while flag:
            data = clientSocket.recv(1024)
            if not data:
                break
            receivedMessage = Message(**json.loads(data))
            if receivedMessage.messageType == 'My Location':
                UserLocation = receivedMessage.messageValue
                distance = math.sqrt((self.ENodeBLocation[0]-UserLocation[0])**2+(self.ENodeBLocation[1]-UserLocation[1])**2)
                sendMessage = Message('User distance', (UserID, distance))
                self.ToMMESocket.send(json.dumps(sendMessage.__dict__).encode("utf-8"))
        self.ServerSocketForUsersSignaling.close()

    def connect_to_Users_for_signaling(self, User):
        ToUsersSocket = socket.socket()
        ToUsersSocket.connect((User.UserHost, 51000))
        self.ToUsersSocketsForSignaling.append(ToUsersSocket)

    def new_connection_from_Users_for_data(self, PreviousENodeB, UserID):
        if not self.ServerSocketForUsersData:
            self.ServerSocketForUsersData = socket.socket()
            self.ServerSocketForUsersData.bind((self.ENodeBHost, 52000))
        self.ServerSocketForUsersData.listen()
        clientSocket, address = self.ServerSocketForUsersData.accept()
        self.connect_to_Users_for_data(UserID)
        if PreviousENodeB != -1:
            sendMessage = Message('Send Me Buffered data', (PreviousENodeB, self.ENodeBID, UserID))
            self.ToSGWSocket.send(json.dumps(sendMessage.__dict__).encode("utf-8"))
        while True:
            data = clientSocket.recv(1024)
            if not data:
                break
            receivedMessage = Message(**json.loads(data))
            if receivedMessage.messageType == 'Create Session':
                SenderID = receivedMessage.messageValue[0]
                ReceiverID = receivedMessage.messageValue[1]
                sendMessage = Message('Create Session', (SenderID, ReceiverID))
                self.ToSGWSocket.send(json.dumps(sendMessage.__dict__).encode("utf-8"))
            if receivedMessage.messageType == 'Create Session Ack':
                SenderID = receivedMessage.messageValue[0]
                ReceiverID = receivedMessage.messageValue[1]
                sendMessage = Message('Create Session Ack', (SenderID, ReceiverID))
                self.ToSGWSocket.send(json.dumps(sendMessage.__dict__).encode("utf-8"))
            if receivedMessage.messageType == 'Data Carrier':
                ReceiverID = receivedMessage.messageValue[0]
                Data = receivedMessage.messageValue[1]
                SequenceNumber = receivedMessage.messageValue[2]
                sendMessage = Message('Data Carrier', (ReceiverID, Data, SequenceNumber))
                self.ToSGWSocket.send(json.dumps(sendMessage.__dict__).encode("utf-8"))
        self.ServerSocketForUsersData.close()

    def connect_to_Users_for_data(self, UserID):
        ToUsersSocketForData = socket.socket()
        ToUsersSocketForData.connect(('127.0.2.' + str(UserID), 53000))
        self.ToUsersSocketsForData = self.ToUsersSocketsForData + ((UserID, ToUsersSocketForData), )
