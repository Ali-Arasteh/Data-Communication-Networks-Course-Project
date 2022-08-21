import socket
import json
import time
import numpy
import threading
from Message import Message


class User:
    def __init__(self, UserID, UserLocations):
        self.UserID = UserID
        self.UserLocations = UserLocations
        self.UserHost = '127.0.2.' + str(self.UserID)
        self.ToENodeBsSocketsForSignaling = []
        self.ServerSocketForENodeBsSignaling = None
        self.ToENodeBSocketForData = None
        self.ServerSocketForENodeBData = None
        self.Ack = False
        self.Flag = True

    def connect_to_eNodeBs_for_signaling(self, ENodeB):
        ToENodeBsSocketForSignaling = socket.socket()
        ToENodeBsSocketForSignaling.connect((ENodeB.ENodeBHost, 50000))
        sendMessage = Message('Signaling channel setup', self.UserID)
        ToENodeBsSocketForSignaling.send(json.dumps(sendMessage.__dict__).encode("utf-8"))
        self.ToENodeBsSocketsForSignaling.append(ToENodeBsSocketForSignaling)

    def new_connection_from_eNodeBs_for_signaling(self):
        if not self.ServerSocketForENodeBsSignaling:
            self.ServerSocketForENodeBsSignaling = socket.socket()
            self.ServerSocketForENodeBsSignaling.bind((self.UserHost, 51000))
        self.ServerSocketForENodeBsSignaling.listen()
        clientSocket, address = self.ServerSocketForENodeBsSignaling.accept()
        while True:
            data = clientSocket.recv(1024)
            if not data:
                break
            receivedMessage = Message(**json.loads(data))
            if receivedMessage.messageType == 'User Registration2':
                NewENodeBHost = receivedMessage.messageValue[0]
                PreviousENodeB = receivedMessage.messageValue[1]
                if self.ToENodeBSocketForData:
                    self.ToENodeBSocketForData.close()
                self.connect_to_eNodeB_for_data(NewENodeBHost)
                threading.Thread(target=self.new_connection_from_eNodeB_for_data).start()
        self.ServerSocketForENodeBsSignaling.close()

    def connect_to_eNodeB_for_data(self, ENodeBHost):
        self.ToENodeBSocketForData = socket.socket()
        self.ToENodeBSocketForData.connect((ENodeBHost, 52000))

    def new_connection_from_eNodeB_for_data(self):
        if not self.ServerSocketForENodeBData:
            self.ServerSocketForENodeBData = socket.socket()
            self.ServerSocketForENodeBData.bind((self.UserHost, 53000))
        self.ServerSocketForENodeBData.listen()
        clientSocket, address = self.ServerSocketForENodeBData.accept()
        while True:
            data = clientSocket.recv(1024)
            if not data:
                break
            receivedMessage = Message(**json.loads(data))
            if receivedMessage.messageType == 'Create Session':
                SenderID = receivedMessage.messageValue[0]
                ReceiverID = receivedMessage.messageValue[1]
                sendMessage = Message('Create Session Ack', (SenderID, ReceiverID))
                self.ToENodeBSocketForData.send(json.dumps(sendMessage.__dict__).encode("utf-8"))
            elif receivedMessage.messageType == 'Create Session Ack':
                self.Ack = True
            elif receivedMessage.messageType == 'Data Carrier':
                Data = receivedMessage.messageValue
                if self.Flag:
                    fileID = open('Received Data.txt', 'w')
                    fileID.writelines(Data)
                    fileID.close()
                    self.Flag = False
                else:
                    fileID = open('Received Data.txt', 'a')
                    fileID.writelines(Data)
                    fileID.close()
        self.ServerSocketForENodeBData.close()
        
    def update_user_location(self):
        for i in range(len(self.UserLocations)):
            sendMessage = Message('My Location', (int(self.UserLocations[i][0]), int(self.UserLocations[i][1])))
            for j in range(len(self.ToENodeBsSocketsForSignaling)):
                self.ToENodeBsSocketsForSignaling[j].send(json.dumps(sendMessage.__dict__).encode("utf-8"))
            time.sleep(10)
