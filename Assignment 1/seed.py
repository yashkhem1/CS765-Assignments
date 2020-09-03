import os
import sys
import socket
import select
import random
import queue

class Seed(object):
    def __init__(self,IP,port,verbose=False):
        self.IP = IP
        self.port = port
        self.peer_list = []
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setblocking(0)
        self.server.bind((self.IP,self.port))
        self.server.listen(5)
        self.sockets_list = [self.server]
        self.sockets_map = {(self.IP,self.port):self.server}
        self.peers_map = {self.server:(self.IP,self.port)}
        self.verbose = verbose

    def write_to_outfile(self,message):
        with open("outfile.txt",'a') as f:
            f.write("Seed "+ str(self.IP)+ ":"+ str(self.port)+" -> " + message+"\n")

    def log(self,message,force_log=False):
        if force_log or self.verbose:
            print(message)
            self.write_to_outfile(message)


    def peer_list_to_string(self):
        peer_string = ""
        for (ip,port) in self.peer_list:
            peer_string+=str(ip)+":"+str(port)+","
        peer_string = peer_string[:-1]
        return peer_string

    def reg_response(self,data_string,socket):
        peer_ip = data_string.split(':')[1]
        peer_port = int(data_string.split(':')[2])
        if (peer_ip,peer_port) in self.peer_list:
            return
        self.peer_list.append((peer_ip,peer_port))
        self.sockets_map[(peer_ip,peer_port)] = socket
        self.peers_map[socket] = (peer_ip,peer_port)
        self.log(data_string,True)
        peer_response = "Registration Successful:"+ self.IP+":"+str(self.port)
        socket.send(peer_response.encode())

    def dead_node_response(self,data_string):
        peer_ip = data_string.split(':')[1]
        peer_port = int(data_string.split(':')[2])
        if (peer_ip,peer_port) in self.peer_list:
            self.peer_list.remove((peer_ip,peer_port))
            conn = self.sockets_map[(peer_ip,peer_port)]
            self.sockets_list.remove(conn)
            self.peers_map.pop(conn)
            self.sockets_map.pop((peer_ip,peer_port))
            conn.close()
        self.log(data_string,True)

    def peer_response(self,s):
        peer_string = ""
        for (peer_ip, peer_port) in self.peer_list:
            peer_string+=peer_ip+":"+str(peer_port)+","
        peer_string = peer_string[:-1]
        s.send(peer_string.encode())



    def run(self):
        print("Seed Running with IP: ", self.IP, "and Port: ", str(port))
        while True:
            readable,_,_ = select.select(self.sockets_list,[],self.sockets_list)
            #Readable
            for s in readable:
                if s is self.server:
                    conn,_ = s.accept()
                    conn.setblocking(0)
                    self.sockets_list.append(conn)

                else:
                    data = s.recv(1024)
                    if data:
                        data_string = str(data.decode())
                        incoming_messages = data_string.split("\0")[:-1]
                        for message in incoming_messages:
                            if message.startswith("Registration Request"):
                                self.reg_response(message,s)

                            elif message.startswith("Dead Node"):
                                self.dead_node_response(message)

                            elif message.startswith("Peer Request"):
                                self.peer_response(s)

                    else:
                        if s in self.sockets_list:
                            self.sockets_list.remove(s)
                            (peer_ip,peer_port) = self.peers_map[s]
                            self.peer_list.remove((peer_ip,peer_port))
                            self.sockets_map.pop((peer_ip,peer_port))
                            self.peers_map.pop(s)
                                    
                        s.close()


if __name__ == "__main__":
    IP = sys.argv[1]
    port = int(sys.argv[2])
    verbose = False
    if len(sys.argv) == 4:
        verbose = bool(int(sys.argv[3]))
    seed = Seed(IP,port,verbose)
    seed.run()
                        
                    
