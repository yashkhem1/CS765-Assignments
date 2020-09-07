import os
import sys
import socket
import select
import random
import queue

class Seed(object):
    def __init__(self,IP,port,verbose=False):
        """Initialization of the seed node

        Args:
            IP (str): IP address of the server
            port (int): Port number of the server
            verbose (bool, optional): Verbose flag to log all the messages sent. Defaults to False.
        """
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
        """Write the message to outfile.txt

        Args:
            message (str): Message to be written
        """
        with open("outfile.txt",'a') as f:
            f.write("Seed "+ str(self.IP)+ ":"+ str(self.port)+" -> " + message+"\n")

    def log(self,message,force_log=False):
        """Logs the message to terminal as well as the outfile

        Args:
            message (str): Message to be logged
            force_log (bool, optional): Log the message even if verbose if False. Defaults to False.
        """
        if force_log or self.verbose:
            print(message)
            self.write_to_outfile(message)

    def reg_response(self,data_string,socket):
        """Send the response to the peer which has sent the registration request

        Args:
            data_string (str): Request sent by the peer
            socket (socket): Socket used for peer connection
        """
        peer_ip = data_string.split(':')[1]
        peer_port = int(data_string.split(':')[2])
        if (peer_ip,peer_port) in self.peer_list:
            return
        self.peer_list.append((peer_ip,peer_port))
        self.sockets_map[(peer_ip,peer_port)] = socket
        self.peers_map[socket] = (peer_ip,peer_port)
        self.log(data_string,True)
        peer_response = "Registration Successful:"+ self.IP+":"+str(self.port)
        self.log(peer_response)
        socket.send(peer_response.encode())

    def dead_node_response(self,data_string):
        """Remove the connection with the dead node on receiving the dead node message

        Args:
            data_string (str): Dead node message sent by the peer
        """
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

    def peer_response(self,s,message):
        """Send the list of connected peers 

        Args:
            s (socket): Socket used for peer connection
            message (str): Request sent by the peer
        """
        self.log(message)
        peer_string = ""
        for (peer_ip, peer_port) in self.peer_list:
            peer_string+=peer_ip+":"+str(peer_port)+","
        peer_string = peer_string[:-1]
        self.log(peer_string)
        s.send(peer_string.encode())



    def run(self):
        """Run process for seed node
        """
        print("Seed Running with IP: ", self.IP, "and Port: ", str(port))
        while True:

            readable,_,_ = select.select(self.sockets_list,[],self.sockets_list)
            for s in readable:
                if s is self.server:
                    #connect with the incoming peer
                    conn,_ = s.accept()
                    conn.setblocking(0)
                    self.sockets_list.append(conn)

                else:
                    #Handle the incoming messages from the peers
                    data = s.recv(1024)
                    if data:
                        data_string = str(data.decode())
                        incoming_messages = data_string.split("\0")[:-1]
                        for message in incoming_messages:
                            if message.startswith("Registration Request"):
                                #Handle the registration request
                                self.reg_response(message,s)

                            elif message.startswith("Dead Node"):
                                #Handle the dead node message
                                self.dead_node_response(message)

                            elif message.startswith("Peer Request"):
                                #Handle the peer request
                                self.peer_response(s,message)

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
                        
                    
