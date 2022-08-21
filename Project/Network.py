import threading
import numpy
import json
import time
from MME import MME
from SGW import SGW
from ENodeB import ENodeB
from User import User
from Message import Message


class Network:
    def __init__(self, ENodeBLocations):
        self.MME = MME('127.0.0.1')
        self.SGW = SGW('127.0.0.2')
        self.ENodeBs = []
        self.NumberOfENodeBs = 0
        self.SendReceiveAbility = False
        self.Users = []
        self.NumberOfUsers = 0
        for i in range(len(ENodeBLocations)):
            eNodeB = ENodeB(self.NumberOfENodeBs, ENodeBLocations[i, :])
            self.ENodeBs.append(eNodeB)
            self.NumberOfENodeBs = self.NumberOfENodeBs + 1

    def init_network(self):
        threading.Thread(target=self.SGW.new_connection_from_MME).start()
        self.MME.connect_to_SGW(self.SGW)
        for i in range(len(self.ENodeBs)):
            threading.Thread(target=self.MME.new_connection_from_eNodeBs).start()
            self.ENodeBs[i].connect_to_MME(self.MME)
            threading.Thread(target=self.SGW.new_connection_from_eNodeBs).start()
            self.ENodeBs[i].connect_to_SGW(self.SGW)
            threading.Thread(target=self.ENodeBs[i].new_connection_from_MME).start()
            self.MME.connect_to_ENodeBs(self.ENodeBs[i])
            threading.Thread(target=self.ENodeBs[i].new_connection_from_SGW).start()
            self.SGW.connect_to_ENodeBs(self.ENodeBs[i])
        self.SendReceiveAbility = True

    def add_user(self, UserID, UserLocations):
        if self.SendReceiveAbility:
            user = User(UserID, UserLocations)
            if self.NumberOfUsers == 0:
                self.MME.UsersToENodeBsDistance = numpy.full((1, self.NumberOfENodeBs), float('inf'))
            else:
                self.MME.UsersToENodeBsDistance = numpy.vstack((self.MME.UsersToENodeBsDistance, numpy.full((1, self.NumberOfENodeBs), float('inf'))))
            self.MME.ClosestENodeBsToUsers.append(-1)
            self.SGW.RoutingTable.append(-1)
            for i in range(len(self.ENodeBs)):
                threading.Thread(target=self.ENodeBs[i].new_connection_from_Users_for_signaling).start()
                user.connect_to_eNodeBs_for_signaling(self.ENodeBs[i])
                threading.Thread(target=user.new_connection_from_eNodeBs_for_signaling).start()
                self.ENodeBs[i].connect_to_Users_for_signaling(user)
                self.ENodeBs[i].SendToUsers.append(0)
                self.ENodeBs[i].UsersBufferedData.append('')
                self.ENodeBs[i].SequenceNumbers.append(-1)
            threading.Thread(target=user.update_user_location).start()
            self.Users.append(user)
            self.NumberOfUsers = self.NumberOfUsers + 1
        else:
            print('First call the init_network function.')

    def connection_request(self, sender_id, receiver_id, file_name):
        if self.SendReceiveAbility:
            sendMessage = Message('Create Session', (sender_id, receiver_id))
            while True:
                if self.Users[sender_id].ToENodeBSocketForData:
                    self.Users[sender_id].ToENodeBSocketForData.send(json.dumps(sendMessage.__dict__).encode("utf-8"))
                    break
            flag = 1
            while flag:
                if self.Users[sender_id].Ack:
                    fileID = open(file_name, 'r')
                    count = 0
                    while True:
                        Data = fileID.readline()
                        if not Data:
                            flag = 0
                            break
                        sendMessage = Message('Data Carrier', (receiver_id, Data, count))
                        self.Users[sender_id].ToENodeBSocketForData.send(json.dumps(sendMessage.__dict__).encode("utf-8"))
                        count = count + 1
                        time.sleep(10)
                    fileID.close()
        else:
            print('First call the init_network function.')
