from blockchain import BlockchainPeer
import os
import argparse
import socket
import numpy as np
import math
import time
import random

class Adversary(BlockchainPeer):
    def __init__(self,IP,port,hash_fraction,inter_arrival_time,network_delay,num_flooded,flood_every,outdir,verbose=False,no_print=False):
        super(Adversary,self).__init__(IP,port,hash_fraction,inter_arrival_time,network_delay,outdir,verbose,no_print)
        self.num_flooded = num_flooded
        self.target_peers = []
        self.flood_every = flood_every
        self.flood_start_time = None

    def generate_invalid_block(self):
        invalid_binary = bin(random.randint(0,2**64-1))[2:]
        return '0'*(64-len(invalid_binary)) + invalid_binary

    def send_invalid_blocks(self):
        invalid_block = self.generate_invalid_block()
        for t in self.peer_sockets:
            if t in self.target_peers:
                self.try_send(("Block:"+invalid_block+"\0").encode(),t)
        self.log("Sent adversarial block "+ hex(int(invalid_block,2))+" Timestamp:"+time.asctime())

    def run(self):
        os.makedirs('outfiles',exist_ok=True)
        print("Adversary Running with IP: ", self.IP, "and Port: ", str(self.port))

        #Get the seeds and peers and establish connection with them
        seed_list = self.get_seeds()
        n_seeds = math.floor(len(seed_list)/2)+1
        seed_list = random.sample(seed_list, n_seeds)
        self.connect_seeds(seed_list)
        peer_list = self.get_peers()
        peer_list.remove((self.IP,self.port))
        peer_list = random.sample(peer_list,min(4,len(peer_list)))
        sync_list = random.sample(peer_list,min(2,len(peer_list)))
        self.connect_peers(peer_list,sync_list)
        self.target_peers = random.sample(self.peer_sockets,self.num_flooded)

        self.reset_time()
        self.viz_start_time = time.time()
        self.flood_start_time = time.time()

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
                            if message.startswith("Block"): #TODO: Include liveness functionality in the blockchain
                                #Add the block to the queue
                                self.receive_block(message,s)

                    else:
                        #Connection  is down
                        curr_time = time.time()
                        self.send_dead_node(s,curr_time)


                except Exception as e :
                    pass

            #Transfer blocks from network queue to validation queue
            self.transfer_to_validation_queue()
            
            #Check if queue is not empty:
            if len(self.validation_queue) > 0:
                self.process_queue()
                self.reset_time()

            #Mine block
            curr_time = time.time()
            if curr_time - self.mine_start_time > self.mine_time:
                self.mine_block()
                self.reset_time()

            #Visualize blockchain
            curr_time = time.time()
            if curr_time - self.viz_start_time > self.viz_time:
                self.visualize_blockchain()
                self.viz_start_time = curr_time

            #Flood the target peers
            curr_time = time.time()
            if curr_time - self.flood_start_time > self.flood_every:
                self.send_invalid_blocks()
                self.flood_start_time = curr_time

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--IP',type=str,help='IP Address of the peer')
    parser.add_argument('--port',type=int, help='Port Number of the peer')
    parser.add_argument('--hash_fraction',type=float, help='Fraction of hashing power peer has')
    parser.add_argument('--inter_arrival_time',type=float, help='Inter Arrival time of the blocks')
    parser.add_argument('--verbose',action='store_true',help='Verbose flag')
    parser.add_argument('--network_delay',type=float,default=2.0,help='Implicit network delay in the network')
    parser.add_argument('--no_print',action='store_true',help='No printing to std out')
    parser.add_argument('--outdir',type=str,default='Output Directory')
    parser.add_argument('--num_flooded',type=int,default=1,help='Number of nodes to be flooded in the network')
    parser.add_argument('--flood_every',type=float,default=0.5,help='Time difference between invalid packets')
    args = parser.parse_args()
    blockchain_peer = Adversary(args.IP,args.port,args.hash_fraction,args.inter_arrival_time,args.network_delay,args.num_flooded, args.flood_every, args.outdir,args.verbose,args.no_print)
    blockchain_peer.run()
    

    
