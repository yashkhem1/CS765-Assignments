import os
import sys
import socket
import select
import random
import hashlib
import math
import time

class Peer(object):
    def __init__(self,IP,port,verbose=False):
        """Initialization of the peer node

        Args:
            IP (string): IP address of the server 
            port (int): Port number of the server
            verbose (bool, optional): Verbose flag to log all the messages sent. Defaults to False.
        """
        self.IP = IP
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setblocking(0)
        self.server.bind((self.IP,self.port))
        self.server.listen(5)
        self.seed_sockets = []
        self.peer_sockets = []
        self.sock_seed_mapping = {}
        self.sock_peer_mapping = {}
        self.message_list = {}
        self.liveness_timer = None
        self.active_bool = {}
        self.inactive_duration = {}
        self.message_timer = None
        self.message_count = 0
        self.message_timeout = 5
        self.liveness_timeout = 13
        self.total_messages = 10
        self.max_inactive_duration = 3
        self.verbose = verbose

    def write_to_outfile(self,message):
        """Write the message to outfile.txt 

        Args:
            message (str): Message to be written
        """
        with open("outfile.txt",'a') as f:
            f.write("Peer "+ str(self.IP)+ ":"+ str(self.port)+" -> " + message+"\n")

    def log(self,message,force_log=False):
        """Logs the message to terminal as well as the outfile

        Args:
            message (str): Message to be logged
            force_log (bool, optional): Log the message even if verbose if False. Defaults to False.
        """
        if self.verbose or force_log:
            print(message)
            self.write_to_outfile(message)

    def try_send(self,message,socket):
        """Try catch version of socket.send

        Args:
            message (str): Message to be sent
            socket (socket): Socket used for sending message
        """
        try:
            socket.send(message)
        except:
            pass

    def get_seeds(self):
        """Get the seeds IP and port info using config file

        Returns:
            List[Tuple]: List of (IP,port) tuples
        """
        seed_list = []
        with open('config.txt','r') as f:
            for lines in f.readlines():
                seed_list.append((lines.split(":")[0],int(lines.split(":")[1])))
        return seed_list

    def connect_seeds(self,seed_list):
        """Connect with the seeds in the seed_list

        Args:
            seed_list (List[Tuple]): List of (IP,port) tuples
        """
        for (seed_ip, seed_port) in seed_list:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((seed_ip,seed_port))
            sock.send(("Registration Request:"+self.IP+":"+str(self.port)+"\0").encode())
            response = sock.recv(1024)
            self.log(response.decode())
            if response.decode().split(":")[0] == "Registration Successful":
                self.seed_sockets.append(sock)
                self.sock_seed_mapping[sock] = (seed_ip,seed_port)
            else:
                sock.close()

    def get_peers(self):
        """Get the peer IP and port information from the connected seeds

        Returns:
            List[Tuple]: List of (IP,port) tuples
        """ 
        peer_list = []
        self.log("Sent Peer Request:"+self.IP+":"+str(self.port))
        for s in self.seed_sockets:
            s.send(("Peer Request:"+self.IP+":"+str(self.port)+"\0").encode())
            peer_string = s.recv(1024).decode()
            (seed_ip,seed_port) = self.sock_seed_mapping[s]
            self.log("Peers connected to " + seed_ip + ":" + str(seed_port) +" => "+peer_string,True)
            for x in peer_string.split(","):
                peer_ip = x.split(":")[0]
                peer_port = int(x.split(":")[1])
                if (peer_ip,peer_port) not in peer_list:
                    peer_list.append((peer_ip,peer_port))
            s.setblocking(0)
        return peer_list


    def connect_peers(self,peer_list):
        """Connect to the peers in the peer_list

        Args:
            peer_list (List[Tuple]): List of (IP,port) tuples
        """
        self.log("Sent Connection Info:"+self.IP+":"+str(self.port))
        for (peer_ip, peer_port) in peer_list:
            if (peer_ip,peer_port) == (self.IP, self.port):
                continue
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((peer_ip,peer_port))
            sock.send(("Connection Info:"+self.IP+":"+str(self.port)).encode())
            response = sock.recv(1024)
            if response.decode() == "Connection Successful":
                self.log("Received"+response.decode()+"from "+peer_ip+":"+str(peer_port))
                sock.setblocking(0)
                self.peer_sockets.append(sock)
                self.sock_peer_mapping[sock] = (peer_ip,peer_port)
                self.active_bool[sock] = True
                self.inactive_duration[sock] = 0
            else:
                sock.close()

    def incoming_peers(self,sock):
        """Connect to the incoming peers

        Args:
            sock (socket): Incoming connection socket 
        """
        request = sock.recv(1024)
        request_string = request.decode()
        self.log("Received "+request_string)
        peer_ip = request_string.split(":")[1]
        peer_port = int(request_string.split(":")[2])
        sock.setblocking(0)
        self.peer_sockets.append(sock)
        self.sock_peer_mapping[sock] = (peer_ip,peer_port)
        self.active_bool[sock] = True
        self.inactive_duration[sock] = 0
        sock.send(b"Connection Successful")
        self.log("Sent Connection Response to "+peer_ip+":"+str(peer_port))

    def send_live_reply(self,peer_string,sock):
        """Send liveness reply to the peer

        Args:
            peer_string (str): Liveness request sent by the peer
            sock (socket): Socket used for the peer connection
        """
        (_,peer_ts,peer_ip,peer_port) = peer_string.split(":")
        live_reply = "Liveness Reply:" + peer_ts +":" + peer_ip+":"+peer_port+":"+self.IP+":"+str(self.port)+"\0"
        self.log("Sent "+ live_reply[:-1])
        sock.send(live_reply.encode()) #TODO: Replace send by try_send and recv by try_receive 


    def reset_liveness(self,peer_string,sock):
        """Reset the liveness variables for the given peer

        Args:
            peer_string (str): Liveness reply sent by the peer
            sock (socket): Socket used for the peer connection
        """
        self.inactive_duration[sock] = 0
        self.active_bool[sock] = True

    def relay_gossip(self,peer_string,parent_sock):
        """Relay the gossip message sent by the paren peer

        Args:
            peer_string (str): Message sent by the parent peer
            parent_sock (socket): Socket used for parent peer connection
        """
        mhash = hash(peer_string)
        if mhash in self.message_list.keys() and self.message_list[mhash]==True:
            pass

        else:
            self.message_list[mhash]= True
            curr_time = time.time()
            (parent_ip,parent_port) = self.sock_peer_mapping[parent_sock]
            message_output = "Local Timestamp: " + str(curr_time) + " Parent IP: " + parent_ip + " Parent Port: " + str(parent_port) + " Message: " + peer_string
            self.log(message_output,True)
            for t in self.peer_sockets:
                if t is parent_sock:
                    continue

                else:
                    self.try_send((peer_string+"\0").encode(),t)

    def send_gossip(self,timestamp):
        """Send the gossip message to all the peers

        Args:
            timestamp (str): Timestamp to be used in the message
        """
        gossip = str(timestamp)+":"+self.IP+":"+str(self.port)+":"+str(self.message_count)+"\0"
        self.log("Sent " + gossip[:-1])
        self.message_list[hash(gossip[:-1])] = True
        for s in self.peer_sockets:
            self.try_send(gossip.encode(),s)
        self.message_count+=1 
        

    def send_dead_node(self,sock,timestamp):
        """Send the dead node message to all the seeds and close connection with the dead node

        Args:
            sock (socket): Socket used for connection with the dead node
            timestamp (str): Timestamp to be used in the message
        """
        (peer_ip,peer_port) = self.sock_peer_mapping[sock]
        dead_message = "Dead Node:"+peer_ip+":"+str(peer_port)+":"+str(timestamp)+":"+self.IP+":"+str(self.port)+"\0"
        self.log(dead_message,True)
        for s in self.seed_sockets:
            self.try_send(dead_message.encode(),s)
        self.peer_sockets.remove(sock)
        self.sock_peer_mapping.pop(sock)
        self.active_bool.pop(sock)
        self.inactive_duration.pop(sock)
        sock.close()

    def send_live_request(self,timestamp):
        """Send the liveness request to all the peer nodes

        Args:
            timestamp (str): Timestamp to be used in the message
        """
        live_request = "Liveness Request:"+str(timestamp)+":"+self.IP+":"+str(self.port)+"\0"
        self.log("Sent "+ live_request[:-1])
        for s in self.peer_sockets:
            self.active_bool[s] = False
            self.try_send(live_request.encode(),s)

    def check_liveness(self,timestamp):
        """Check the liveness of the peer nodes

        Args:
            timestamp (str): Timestampe to be used in the dead node message
        """
        for s in self.peer_sockets:
            if self.active_bool[s] == False:
                self.inactive_duration[s]+=1
                if self.inactive_duration[s] == self.max_inactive_duration:
                    self.send_dead_node(s,timestamp)
        

    def run(self):
        """Run process for the peer node
        """
        print("Peer Running with IP: ", self.IP, "and Port: ", str(port))

        #Get the seeds and peers and establish connection with them
        seed_list = self.get_seeds()
        n_seeds = math.floor(len(seed_list)/2)+1
        seed_list = random.sample(seed_list, n_seeds)
        self.connect_seeds(seed_list)
        peer_list = self.get_peers()
        peer_list.remove((self.IP,self.port))
        peer_list = random.sample(peer_list,min(4,len(peer_list)))
        self.connect_peers(peer_list)
        curr_time = time.time()

        #Send the first set of gossip messages and liveness request to the connected peers
        self.send_gossip(curr_time)
        self.message_timer = curr_time
        self.send_live_request(curr_time)
        self.liveness_timer = curr_time
        
        while(True):
            #Check if connections to seeds is intact
            try:
                connected = 1
                for s in self.seed_sockets:
                    data = s.recv(1024)
                    if not data:
                        connected = 0
                        break
                if connected == 0:
                    break

            except Exception as e:
                pass

            #Server Check if there are any incoming connections
            try:
                conn,_ = self.server.accept()
                self.incoming_peers(conn)

            except Exception as e:
                pass
            
            #Check for any incoming messages from other peers
            for s in self.peer_sockets:
                try:
                    peer_data = s.recv(1024)
                    if peer_data:
                        peer_string = peer_data.decode()
                        peer_messages = peer_string.split("\0")[:-1]
                        for message in peer_messages:
                            if message.startswith("Liveness Request"):
                                #Send liveness reply
                                self.log("Received "+message)
                                self.send_live_reply(message,s)

                            elif message.startswith("Liveness Reply"):
                                #Reset liveness variables
                                self.log("Received "+message)
                                self.reset_liveness(message,s)

                            else:
                                #Relay the gossip to connected peers
                                self.relay_gossip(message,s)

                    else:
                        #Connection is down
                        curr_time = time.time()
                        self.send_dead_node(s,curr_time)


                except Exception as e :
                    pass
            
            #Send gossip message
            
            curr_time = time.time()
            if self.message_count<self.total_messages:
                if (curr_time - self.message_timer) >= self.message_timeout:
                    self.message_timer = curr_time
                    self.send_gossip(curr_time)

            
            
            # Send liveness message and check liveness
            
            curr_time = time.time()
            if (curr_time - self.liveness_timer) >= self.liveness_timeout:
                self.liveness_timer = curr_time
                self.check_liveness(curr_time)
                self.send_live_request(curr_time)

            
            

if __name__ =="__main__":
    IP = sys.argv[1]
    port = int(sys.argv[2])
    verbose = False
    if len(sys.argv) ==4:
        verbose = True
    peer = Peer(IP,port,verbose)
    peer.run()


