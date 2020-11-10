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
import argparse
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
        self.mined = mined

    def __str__(self):
        prev_hash_str = bin(self.prev_hash)[2:]
        prev_hash_str = '0'*(16-len(prev_hash_str)) + prev_hash_str
        merkel_root_str = bin(self.merkel_root)[2:]
        merkel_root_str = '0'*(16-len(merkel_root_str)) + merkel_root_str
        timestamp_str = bin(int(self.timestamp))[2:]
        timestamp_str = '0'*(32-len(timestamp_str)) + timestamp_str
        return prev_hash_str + merkel_root_str + timestamp_str

class BlockchainPeer(Peer):
    def __init__(self,IP,port,hash_fraction,inter_arrival_time,network_delay,outdir,verbose=False,no_print=False,terminate_after=10000000):
        super(BlockchainPeer,self).__init__(IP,port,outdir,verbose,no_print)
        self.level_tree = []
        self.longest_chain_block = None
        self.hash_fraction = hash_fraction
        self.inter_arrival_time = inter_arrival_time
        self.network_delay = network_delay
        self.terminate_after = terminate_after
        self.block_hash = {}
        self.message_hash = {}
        self.validation_queue = []
        self.network_queue = []
        self.genesis_hash = bin(int('0x9e1c',16))[2:]
        self.start_time = None
        self.mine_time = None
        self.mine_start_time = None
        self.viz_time = 2
        self.viz_start_time = None
        #self.peer_hash = {} TODO:Dynamic hashing power instead of static

    def validate_block(self,block_header):
        assert(len(block_header)==64)
        if not self.check_timestamp(block_header):
            self.log("Inavlid block "+hex(int(block_header,2)))
            return 0 
        prev_hash = block_header[:16]
        if hash(block_header) in self.block_hash:
            return 0
        
        if prev_hash == self.genesis_hash:
            prev_length = len(self.level_tree)
            if prev_length == 0:
                self.level_tree.append([])
            b = Block(int(prev_hash,2),int(block_header[16:32],2),int(block_header[32:],2),None,False)
            self.block_hash[hash(block_header)] = True
            self.level_tree[0].append(b)
            if prev_length == 0:
                self.longest_chain_block = b
            self.log("Genesis Block " + hex(int(block_header,2)) + " validated Timestamp:"+str(time.asctime()),force_log=True)
            return 1
        
        for i in range(len(self.level_tree)-1,-1,-1):
            for block in self.level_tree[i]:
                hash_hex = hashlib.sha256(str(block).encode()).hexdigest()[-4:]
                hash_bin = bin(int(hash_hex,16))[2:]
                hash_bin = '0' * (16-len(hash_bin)) + hash_bin
                if prev_hash == hash_bin:
                    prev_length = len(self.level_tree)
                    if i == prev_length-1:
                        self.level_tree.append([])
                    b = Block(int(prev_hash,2),int(block_header[16:32],2),int(block_header[32:],2),block,False)
                    self.block_hash[hash(block_header)] = True
                    self.level_tree[i+1].append(b)
                    self.log("Block header "+hex(int(block_header,2))+" validated Timestamp:"+str(time.asctime()),force_log=True)
                    if i ==prev_length-1:
                        self.longest_chain_block = b
                        self.log("Block is part of the longest chain",force_log=True)
                    return 1

        self.log("Inavlid block "+block_header)
        return 0

    def check_timestamp(self,block_header):
        timestamp = int(block_header[32:],2)
        return abs(timestamp-time.time()) < 3600

    def generate_exp_time(self):
        return np.random.exponential()*self.inter_arrival_time/self.hash_fraction

    def connect_peers(self,peer_list,sync_list):
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
                self.log("Received "+response.decode()+" from "+peer_ip+":"+str(peer_port))
                self.peer_sockets.append(sock)
                self.sock_peer_mapping[sock] = (peer_ip,peer_port)
                self.active_bool[sock] = True
                self.inactive_duration[sock] = 0
                if (peer_ip,peer_port) in sync_list:
                    self.request_blocks(sock)
                else:
                    self.try_send(b"Sync Complete",sock)
                    sock.setblocking(0)
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
        self.peer_sockets.append(sock)
        self.sock_peer_mapping[sock] = (peer_ip,peer_port)
        self.active_bool[sock] = True
        self.inactive_duration[sock] = 0
        sock.send(b"Connection Successful")
        response = sock.recv(1024).decode()
        if response == 'Sync Complete':
            sock.setblocking(0)
        elif response == 'Blocks Request':
            self.send_blocks(sock)
        self.log("Sent Connection Response to "+peer_ip+":"+str(peer_port))
    
    def request_blocks(self,sock):
        self.try_send(b"Blocks Request",sock)
        n_levels = int(sock.recv(1024).decode())
        self.try_send(b"ACK",sock)
        for _ in range(n_levels):
            n_blocks = int(sock.recv(1024).decode())
            self.try_send(b"ACK",sock)
            for _ in range(n_blocks):
                block_header = sock.recv(1024).decode()
                self.try_send(b"ACK",sock)
                _ = self.validate_block(block_header)
        response = sock.recv(1024).decode()
        if response == "All Blocks sent":
            (peer_ip,peer_port) = self.sock_peer_mapping[sock]
            self.try_send(b"Sync Complete",sock)
            sock.setblocking(0)
            self.log("Blockchain sync complete with peer IP:" + peer_ip +" Port:" + str(peer_port) +" Timestamp:"+str(time.asctime()),force_log=True)

    def send_blocks(self,peer_sock):
        self.try_send((str(len(self.level_tree))).encode(),peer_sock)
        ack = peer_sock.recv(1024).decode()  #TODO: Check if ACKs send are good
        for i in range(len(self.level_tree)):
            self.try_send((str(len(self.level_tree[i]))).encode(),peer_sock)
            ack = peer_sock.recv(1024).decode()
            for block in self.level_tree[i]:
                self.try_send((str(block)).encode(),peer_sock)
                ack = peer_sock.recv(1024).decode()
        self.try_send(b"All Blocks sent",peer_sock)
        message = peer_sock.recv(1024).decode()
        if message == "Sync Complete":
            peer_sock.setblocking(0)
            (peer_ip,peer_port) = self.sock_peer_mapping[peer_sock]
            self.log("Synced blockchain with peer IP:"+peer_ip+" Port:"+str(peer_port)+" Timestamp:"+str(time.asctime()),force_log=True)

    def reset_mine(self):
        self.mine_start_time = time.time()
        self.mine_time = self.generate_exp_time()

    def mine_block(self):
        if self.longest_chain_block is None:
            prev_hash = int(self.genesis_hash,2)
        else:
            hash_hex = hashlib.sha256(str(self.longest_chain_block).encode()).hexdigest()[-4:]
            prev_hash = int(hash_hex,16)
        merkel_root = np.random.randint(0,65535)
        timestamp = int(time.time())
        b = Block(prev_hash,merkel_root,timestamp,self.longest_chain_block,True)
        self.level_tree.append([])
        self.level_tree[-1].append(b)
        # if self.longest_chain_block:
        #     print(hex(int(str(self.longest_chain_block),2)),'idhar')
        # else:
        #     print(None,'idhar')
        self.longest_chain_block = b
        message = "Block:"+str(b)+"\0"
        self.message_hash[hash(message[:-1])] = True
        for t in self.peer_sockets:
            self.try_send(message.encode(),t)
        self.log("Mined block: "+hex(int(str(b),2))+" Timestamp:"+str(time.asctime()),force_log=True)
        # print(self.level_tree)


    def receive_block(self,message,parent_sock):
        mhash = hash(message)
        if mhash in self.message_hash:
            return
        block_header = message.split(":")[1]
        self.network_queue.append(((block_header,parent_sock),time.time()))
        self.message_hash[hash(message)] = True

    def transfer_to_validation_queue(self):
        while(True):
            if len(self.network_queue) > 0:
                header_data,timestamp = self.network_queue[0]
                curr_time = time.time()
                if curr_time - timestamp > self.network_delay:
                    self.validation_queue.append(header_data)
                    self.log("Block received:"+hex(int(header_data[0],2))+" Timestamp:"+str(time.asctime()))
                    self.network_queue = self.network_queue[1:]
                else:
                    break
            else:
                break

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
                self.mine_time = self.generate_exp_time()
        self.validation_queue = []
        # print(self.level_tree)

    def visualize_blockchain(self):
        #TODO: Replace it with Ajay's version of tree
        longest_chain = []
        x = self.longest_chain_block
        while(x):
            longest_chain.append(x)
            x = x.prev_block
        longest_chain.reverse()

        total_blocks = 0
        with open(os.path.join(self.outdir,'blockchain_'+self.IP+'_'+str(self.port))+'.txt','w') as w:
            for level in range(len(self.level_tree)):
                total_blocks+=1
                hex_header = hex(int(str(longest_chain[level]),2))
                is_mined = "1" if longest_chain[level].mined else "0"
                w.write(hex_header+":"+is_mined+" ")
                for block in self.level_tree[level]:
                    if block == longest_chain[level]:
                        continue
                    total_blocks+=1
                    hex_header = hex(int(str(block),2))
                    is_mined = "1" if block.mined else "0"
                    w.write(hex_header+":"+is_mined+" ")

                w.write("\n")

            if total_blocks > 0:
                mining_power_utilization = len(longest_chain)/total_blocks
                fraction_mined_in_lc = len([x for x in longest_chain if x.mined])/len(longest_chain)
            else:
                mining_power_utilization = None
                fraction_mined_in_lc = None
            w.write("Mining Power Utilization: "+str(mining_power_utilization)+"\n")
            w.write("Fraction Mined in Longest Chain: "+str(fraction_mined_in_lc))

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
        sync_list = random.sample(peer_list,min(2,len(peer_list)))
        self.connect_peers(peer_list,sync_list)
        self.reset_mine()
        self.start_time = time.time()
        self.viz_start_time = time.time()

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
                self.mine_start_time = time.time()

            #Mine block
            curr_time = time.time()
            if curr_time - self.mine_start_time > self.mine_time:
                self.mine_block()
                self.reset_mine()

            #Visualize blockchain
            curr_time = time.time()
            if curr_time - self.viz_start_time > self.viz_time:
                self.visualize_blockchain()
                self.viz_start_time = curr_time

            #Terminate peer
            curr_time = time.time()
            if curr_time - self.start_time > self.terminate_after:
                self.server.close()
                exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--IP',type=str,help='IP Address of the peer')
    parser.add_argument('--port',type=int, help='Port Number of the peer')
    parser.add_argument('--hash_fraction',type=float, help='Fraction of hashing power peer has')
    parser.add_argument('--inter_arrival_time',type=float, help='Inter Arrival time of the blocks')
    parser.add_argument('--verbose',action='store_true',help='Verbose flag')
    parser.add_argument('--network_delay',type=float,default=1.0,help='Implicit network delay in the network')
    parser.add_argument('--no_print',action='store_true',help='No printing to std out')
    parser.add_argument('--outdir',type=str,help='Output Directory')
    parser.add_argument('--terminate_after',type=float,default=600,help='Seconds after which program needs to be terminated')
    args = parser.parse_args()
    blockchain_peer = BlockchainPeer(args.IP,args.port,args.hash_fraction,args.inter_arrival_time,args.network_delay,args.outdir,args.verbose,args.no_print,args.terminate_after)
    blockchain_peer.run()