import os
import sys
import socket
import select
import random
import hashlib
import math
import time

class Peer(object):
    def __init__(self,IP,port):
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
        self.message_timeout = 3
        self.liveness_timeout = 5

    def write_to_outfile(self,message):
        with open("outfile.txt",'a') as f:
            f.write("Peer "+ str(self.IP)+ ":"+ str(self.port)+" -> " + message+"\n")

    def get_seeds(self):
        seed_list = []
        with open('config.txt','r') as f:
            for lines in f.readlines():
                seed_list.append((lines.split(":")[0],int(lines.split(":")[1])))
        return seed_list

    def connect_seeds(self,seed_list):
        for (seed_ip, seed_port) in seed_list:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((seed_ip,seed_port))
            sock.send(("Registration Request:"+self.IP+":"+str(self.port)).encode())
            response = sock.recv(1024)
            print(response.decode())
            if response.decode() == "Registration Successful":
                self.seed_sockets.append(sock)
                self.sock_seed_mapping[sock] = (seed_ip,seed_port)
            else:
                sock.close()

    def get_peers(self):
        peer_list = []
        for s in self.seed_sockets:
            s.send(("Peer Request:"+self.IP+":"+str(self.port)).encode())
            peer_string = s.recv(1024).decode()
            print(peer_string)
            self.write_to_outfile(peer_string)
            for x in peer_string.split(","):
                peer_ip = x.split(":")[0]
                peer_port = int(x.split(":")[1])
                if (peer_ip,peer_port) not in peer_list:
                    peer_list.append((peer_ip,peer_port))
            s.setblocking(0)
        return peer_list


    def connect_peers(self,peer_list):
        for (peer_ip, peer_port) in peer_list:
            if (peer_ip,peer_port) == (self.IP, self.port):
                continue
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((peer_ip,peer_port))
            sock.send(("Connection Info:"+self.IP+":"+str(self.port)).encode())
            response = sock.recv(1024)
            if response.decode() == "Connection Successful":
                sock.setblocking(0)
                self.peer_sockets.append(sock)
                self.sock_peer_mapping[sock] = (peer_ip,peer_port)
                self.active_bool[sock] = True
                self.inactive_duration[sock] = 0
            else:
                sock.close()

    def incoming_peers(self,sock):
        request = sock.recv(1024)
        request_string = request.decode()
        print(request_string)
        peer_ip = request_string.split(":")[1]
        peer_port = int(request_string.split(":")[2])
        sock.setblocking(0)
        self.peer_sockets.append(sock)
        self.sock_peer_mapping[sock] = (peer_ip,peer_port)
        self.active_bool[sock] = True
        self.inactive_duration[sock] = 0
        sock.send(b"Connection Successful")

    def send_live_reply(self,peer_string,sock):
        print(peer_string)
        self.write_to_outfile(peer_string)
        (_,peer_ts,peer_ip,peer_port) = peer_string.split(":")
        live_reply = "Liveness Reply:" + peer_ts +":" + peer_ip+":"+peer_port+":"+self.IP+":"+str(self.port)
        sock.send(live_reply.encode())


    def reset_liveness(self,peer_string,sock):
        print(peer_string)
        self.write_to_outfile(peer_string)
        self.inactive_duration[sock] = 0
        self.active_bool[sock] = True

    def relay_gossip(self,peer_string,parent_sock):
        mhash = hash(peer_string)
        if mhash in self.message_list.keys() and self.message_list[mhash]==True:
            pass

        else:
            self.message_list[mhash]= True
            curr_time = time.time()
            (parent_ip,parent_port) = self.sock_peer_mapping[parent_sock]
            message_output = "Local Timestamp: " + str(curr_time) + " Parent IP: " + parent_ip + " Parent Port: " + str(parent_port) + " Message: " + peer_string
            print(message_output)
            self.write_to_outfile(message_output)
            for t in self.peer_sockets:
                if t is parent_sock:
                    continue

                else:
                    t.send(peer_string.encode())

    def send_gossip(self,timestamp):
        gossip = str(timestamp)+":"+self.IP+":"+str(self.port)+":"+str(self.message_count)
        for s in self.peer_sockets:
            s.send(gossip.encode())
        self.message_count+=1 
        

    def send_dead_node(self,sock,timestamp):
        (peer_ip,peer_port) = self.sock_peer_mapping[sock]
        dead_message = "Dead Node:"+peer_ip+":"+str(peer_port)+":"+str(timestamp)+":"+self.IP+":"+str(self.port)
        print(dead_message)
        self.write_to_outfile(dead_message)
        for s in self.seed_sockets:
            s.send(dead_message.encode())
        self.peer_sockets.remove(sock)
        self.sock_peer_mapping.pop(sock)
        self.active_bool.pop(sock)
        self.inactive_duration.pop(sock)
        sock.close()

    def send_live_request(self,timestamp):
        live_request = "Liveness Request:"+str(timestamp)+":"+self.IP+":"+str(self.port)
        for s in self.peer_sockets:
            self.active_bool[s] = False
            s.send(live_request.encode())

    def check_liveness(self,timestamp):
        for s in self.peer_sockets:
            if self.active_bool[s] == False:
                self.inactive_duration[s]+=1
                if self.inactive_duration[s] == 3:
                    self.send_dead_node(s,timestamp)
        

    def run(self):
        print("Peer Running with IP: ", self.IP, "and Port: ", str(port))
        seed_list = self.get_seeds()
        n_seeds = math.floor(len(seed_list)/2)+1
        seed_list = random.sample(seed_list, n_seeds)
        self.connect_seeds(seed_list)
        peer_list = self.get_peers()
        peer_list = random.sample(peer_list,min(4,len(peer_list)))
        self.connect_peers(peer_list)
        self.liveness_timer = time.time()
        self.message_timer = time.time()
        sent_message = False
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
                # print(e)
                pass
            
            #Check for any incoming messages from other peers
            for s in self.peer_sockets:
                try:
                    peer_data = s.recv(1024)
                    if peer_data:
                        peer_string = peer_data.decode()
                        if peer_string.startswith("Liveness Request"):
                            self.send_live_reply(peer_string,s)

                        elif peer_string.startswith("Liveness Reply"):
                            self.reset_liveness(peer_string,s)

                        else:
                            self.relay_gossip(peer_string,s)

                    else:
                        #Connection is down
                        curr_time = time.time()
                        self.send_dead_node(s,curr_time)


                except Exception as e :
                    # print(e)
                    pass
            
            #Send gossip message
            try:
                curr_time = time.time()
                if self.message_count<10:
                    if (curr_time - self.message_timer) >= self.message_timeout:
                        self.message_timer = curr_time
                        self.send_gossip(curr_time)

            except Exception as e:
                # print(e)
                pass
            
            # Send liveness message and check liveness
            try:
                curr_time = time.time()
                if (curr_time - self.liveness_timer) >= self.liveness_timeout:
                    self.liveness_timer = curr_time
                    if sent_message == False:
                        sent_message = True
                    else:
                        self.check_liveness(curr_time)

                    self.send_live_request(curr_time)

            
            except Exception as e:
                # print(e)
                pass

if __name__ =="__main__":
    IP = sys.argv[1]
    port = int(sys.argv[2])
    peer = Peer(IP,port)
    peer.run()


