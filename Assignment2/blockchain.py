from peer import Peer
from seed import Seed
import hashlib
import time
import sys
import random
import socket
import numpy as np
import os
import math
class Block(object):
    def __init__ (self,prev_hash,merkel_root,timestamp,prev_block=None,mined=False):
        """Initialize the Blockchain block

        Args:
            prev_hash (int): Hash of the prev block in integer
            merkel_root (int): Random number (for this assignment)
            timestamp (int): Timestamp of block generation
        """
        self.prev_hash = prev_hash
        self.merkel_root = merkel_root
        self.timestamp = timestamp
        self.prev_block = prev_block
        self.mined = False

    def __str__(self):
        prev_hash_str = bin(self.prev_hash)[2:]
        prev_hash_str = '0'*(16-len(prev_hash_str)) + prev_hash_str
        merkel_root_str = bin(self.merkel_root)[2:]
        merkel_root_str = '0'*(16-len(merkel_root_str)) + merkel_root_str
        timestamp_str = bin(int(self.timestamp))[2:]
        timestamp_str = '0'*(32-len(timestamp_str)) + timestamp_str
        return prev_hash_str + merkel_root_str + timestamp_str

class BlockchainPeer(Peer):
    def __init__(self,IP,port,hash_fraction,inter_arrival_time,verbose=False):
        super(BlockchainPeer,self).__init__(IP,port,verbose)
        self.level_tree = []
        self.longest_chain_block = None
        self.hash_fraction = hash_fraction
        self.inter_arrival_time = inter_arrival_time
        self.block_hash = {}
        self.message_hash = {}
        self.validation_queue = []
        self.genesis_hash = bin(int('0x9e1c',16))[2:]
        self.mine_time = None
        self.start_time = None
        #self.peer_hash = {} TODO:Dynamic hashing power instead of static

    def validate_block(self,block_header):
        assert(len(block_header==64))
        if not self.check_timestamp(block_header):
            return 0 
        prev_hash = block_header[:16]
        if self.block_hash[block_header]:
            return 0
        
        if prev_hash == self.genesis_hash:
            if len(self.level_tree) == 0:
                self.level_tree.append([])
            b = Block(int(prev_hash,2),int(block_header[16:32],2),int(block_header[32:],2),None,False)
            self.block_hash[block_header] = True
            self.level_tree[0].append(b)
            self.log("Genesis Block Timestamp:"+str(int(time.time())))
            return 1
        
        for i in range(len(self.level_tree)-1,-1,-1):
            for block in self.level_tree[i]:
                hash_hex = hashlib.sha256(str(block).encode()).hexdigest()[-4:]
                hash_bin = bin(int(hash_hex,16))[2:]
                if prev_hash == hash_bin:
                    if i == len(self.level_tree)-1:
                        self.level_tree.append([])
                    b = Block(int(prev_hash,2),int(block_header[16:32],2),int(block_header[32:],2),block,False)
                    self.block_hash[block_header] = True
                    self.level_tree[i+1].append(b)
                    self.log("Block header "+block_header+" validated Timestamp:"+str(int(time.time())))
                    if i ==len(self.level_tree)-1:
                        self.longest_chain_block = b
                        self.log("Block is part of the longest chain")
                    return 1

        self.log("Inavlid block "+block_header)
        return 0

    def check_timestamp(self,block_header):
        timestamp = int(block_header[32:],2)
        return abs(timestamp-time.time()) < 3600
    
    def generate_exp_time(self):
        return np.random.exponential()*self.inter_arrival_time/self.hash_fraction
    
    def request_blocks(self,peer_socks):
        for sock in peer_socks:
            sock.setblocking(1)
            self.try_send(b"Blocks Request\0",sock)
            n_levels = int(sock.recv(1024).decode()[:-1])
            self.try_send(b"ACK\0",sock)
            for _ in range(n_levels):
                n_blocks = int(sock.recv(1024).decode()[:-1])
                self.try_send(b"ACK\0",sock)
                for _ in range(n_blocks):
                    block_header = sock.recv(1024).decode()[:-1]
                    self.try_send(b"ACK\0",sock)
                    _ = self.validate_block(block_header)
            sock.setblocking(0)
        self.log("Blockchain sync complete Timestamp:"+str(int(time.time())))

    def send_blocks(self,peer_sock):
        peer_sock.setblocking(1)
        self.try_send((str(len(self.level_tree))+"\0").encode(),peer_sock)
        ack = peer_sock.recv(1024).decode()[:-1]  #TODO: Check if ACKs send are good
        for i in range(len(self.level_tree)):
            self.try_send((str(len(self.level_tree[i]))+"\0").encode(),peer_sock)
            ack = peer_sock.recv(1024).decode()[:-1]
            for block in self.level_tree[i]:
                self.try_send((str(block)+"\0").encode(),peer_sock)
                ack = peer_sock.recv(1024).decode()[:-1]
        peer_sock.setblocking(0)
        (peer_ip,peer_port) = self.sock_peer_mapping[peer_sock]
        self.log("Synced blockchain with peer IP:"+peer_ip+" Port:"+peer_port+" Timestamp:"+int(time.time()))

    def reset_time(self):
        self.start_time = time.time()
        self.mine_time = self.generate_exp_time()

    def mine_block(self):
        prev_hash = self.longest_chain_block.prev_hash
        merkel_root = np.random.randint(0,65535)
        timestamp = int(time.time())
        b = Block(prev_hash,merkel_root,timestamp,self.longest_chain_block,True)
        self.level_tree.append([])
        self.level_tree[-1].append(b)
        self.longest_chain_block = b
        message = "Block:"+str(b)+"\0"
        self.message_hash[hash(message[:-1])] = True
        for t in self.peer_sockets:
            self.try_send(message,t)
        self.log("Mined block: "+str(b)+" Timestamp:"+int(time.time()))


    def receive_block(self,message,parent_sock):
        mhash = hash(message)
        if mhash in self.message_hash:
            return
        block_header = message.split(":")[1]
        self.validation_queue.append((block_header,parent_sock))
        self.log("Block received:"+block_header+" Timestamp:"+int(time.time()))

    
    def process_queue(self):
        for (header,parent_sock) in self.validation_queue:
            success = self.validate_block(header)
            if success:
                message = "Block:"+header+"\0"
                for t in self.peer_sockets:
                    if t is parent_sock:
                        continue
                    else:
                        self.try_send((message).encode(),t)
        self.validation_queue = []

    def run(self):
        os.makedirs('outfiles',exist_ok=True)
        print("Peer Running with IP: ", self.IP, "and Port: ", str(self.port))

        #Get the seeds and peers and establish connection with them
        seed_list = self.get_seeds()
        n_seeds = math.floor(len(seed_list)/2)+1
        seed_list = random.sample(seed_list, n_seeds)
        self.connect_seeds(seed_list)
        peer_list = self.get_peers()
        peer_list.remove((self.IP,self.port))
        peer_list = random.sample(peer_list,min(4,len(peer_list)))
        self.connect_peers(peer_list)
        self.request_blocks(np.random.choice(np.array(self.peer_sockets),min(2,len(self.peer_sockets))))
        self.reset_time()

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
                            if message.startswith("Blocks Request"): #TODO: Include liveness functionality in the blockchain
                                #Send the blocks in the blockchain
                                self.send_blocks(s)

                            elif message.startswith("Block:"):
                                #Add the block to the queue
                                self.receive_block(message,s)

                    else:
                        #Connection is down
                        curr_time = time.time()
                        self.send_dead_node(s,curr_time)


                except Exception as e :
                    pass

            #Check if queue is not empty:
            if len(self.validation_queue) > 0:
                self.process_queue()
                self.reset_time()

            #Mine block
            curr_time = time.time()
            if curr_time - self.start_time > self.mine_time:
                self.mine_block()
                self.reset_time()


if __name__ == "__main__":
    # a = Block(1234,2342,)
    # print(len(str(a)))
    print("hello")