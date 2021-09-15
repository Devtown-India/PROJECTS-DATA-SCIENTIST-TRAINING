# TO CONNECT WITH THE SERVER #

import socket
import pickle


class Network:
    #init method
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #server id
        self.server = "127.0.0.1"
        #port id
        self.port = 5005
        self.addr = (self.server, self.port)
        self.p = self.connect()
        
    #get player id
    def getP(self):
        return self.p

    #connect
    def connect(self):
        try:
            self.client.connect(self.addr)
            return self.client.recv(4096).decode()
        except:
            pass
    
    #send req
    def send(self, data):
        try:
            self.client.send(str.encode(data))
            return pickle.loads(self.client.recv(4096*2))
        except socket.error as e:
            print(e)
