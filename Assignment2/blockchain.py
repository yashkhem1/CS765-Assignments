from peer import Peer
from seed import Seed
import hashlib
import time
import sys
import random
import socket
import numpy as np

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
        self.validation_queue = []
        self.genesis_hash = bin(int('0x9e1c',16))[2:]
        #self.peer_hash = {} TODO:Dynamic hashing power instead of static

    def validate_block(self,block_header):
        assert(len(block_header==64))
        prev_hash = block_header[:16]
        if self.block_hash[block_header]:
            return
        
        if prev_hash == self.genesis_hash:
            if len(self.level_tree) == 0:
                self.level_tree.append([])
            b = Block(int(prev_hash,2),int(block_header[16:32],2),int(block_header[32:],2),None,False)
            self.block_hash[block_header] = True
            self.level_tree[0].append(b)
            self.log("Genesis Block")
            return
        
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
                    self.log("Block header "+block_header+" validated")
                    if i ==len(self.level_tree)-1:
                        self.longest_chain_block = b
                        self.log("Block is part of the longest chain")
                    return

        self.log("Inavlid block "+block_header)
    
    def generate_exp_time(self):
        return np.random.exponential()*self.inter_arrival_time/self.hash_fraction
    
    def request_blocks(self,peer_list):
        for sock in peer_list:
            sock.setblocking(1)
            self.try_send(b"Blocks request\0",sock)
            n_levels = int(sock.recv(1024).decode()[:-1])
            self.try_send(b"ACK\0",sock)
            for i in range(n_levels):
                n_blocks = int(sock.recv(1024).decode()[:-1])
                self.try_send(b"ACK\0",sock)
                for j in range(n_blocks):
                    block_header = sock.recv(1024).decode()[:-1]
                    self.try_send(b"ACK\0",sock)
                    self.validate_block(block_header)
            sock.setblocking(0)
                
        

if __name__ == "__main__":
    # a = Block(1234,2342,)
    # print(len(str(a)))
    print("hello")