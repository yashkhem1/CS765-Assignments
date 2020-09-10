import os
import sys
import socket
import select
import random
import hashlib
import math
import time
from peer import Peer

class MaliciousPeer(Peer):
    def __init__(self,IP,port,verbose=False):
        """Initialization for the malicious peer node

        Args:
            IP (str): IP Address of the server
            port (int): Port number of the server
            verbose (bool, optional): Verbose flag to log all the messages sent. Defaults to False.
        """
        super(MaliciousPeer,self).__init__(IP,port,verbose=False)

    def run(self):
        """Run process for the malicious node
        """
        os.makedirs('outfiles',exist_ok=True)
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

        #Since it is a malicious node, it will not send liveness request or gossip message
        self.liveness_timer = curr_time
        self.message_timer = curr_time
        
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
                        #Since this is malicious node, do nothing on receiving the data
                        pass

                    else:
                        #Connection is down
                        pass


                except Exception as e :
                    pass

            
            

if __name__ =="__main__":
    IP = sys.argv[1]
    port = int(sys.argv[2])
    verbose = False
    if len(sys.argv) ==4:
        verbose = True
    peer = MaliciousPeer(IP,port,verbose)
    peer.run()


