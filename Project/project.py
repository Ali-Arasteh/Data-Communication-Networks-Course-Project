import numpy
import time
from Network import Network

ENodeBLocations = numpy.array([[25, 25], [25, 75], [75, 25], [75, 75]])
UsersLocations = numpy.array([[[20, 10], [40, 10], [60, 10], [80, 10]], [[80, 90], [60, 90], [40, 90], [20, 90]]])
network = Network(ENodeBLocations)
network.init_network()
for i in range(len(UsersLocations)):
    network.add_user(i, UsersLocations[i, :, :])
time.sleep(5)
network.connection_request(0, 1, 'Data.txt')
