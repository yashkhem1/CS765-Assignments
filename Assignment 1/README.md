# Assignment 1
## Gossip protocol implemented in a simple peer-to-peer network
### Team : Yash Khemchandani (170050025), Devansh Garg(170050029), Ajay Sheoran(170050042)

* ### <b>Files present</b>
    1. seed.py
        - Contains the code for the seeds in the P2P network
        - Uses TCP sockets and implemented using socket and select modules in Python

    2. peer.py
        - Contains the code for peers in the P2P network
        - Uses TCP sockets and implemented using socket module in Python

    3. malicious_peer.py
        - Contains the code for malicious peer that reads the messages but doesn't send any message or replies
        - Uses TCP sockets and implemented using socket module in Python
        - Seen as a derieved class for peer class

    4. config.txt
        - Contains the IP and port information for the seeds in the P2P network
        - Used by the incoming peers to connect to the seeds

    5. outfile.txt
        - File where the messages logged are dumped into
        - All the nodes in the same machine use this file

* ### <b>Instructions to run the code</b>
    1. Modify config.txt to contain the information of the seeds in the network
        - Every line should contain \<seed_IP\>:\<seed_port\>

    2.  Start the seeds in the network by running seed.py file with the given IP and port <br>
        `python3 seed.py <seed_IP> <seed_port> <verbose>` where
        - \<seed_ip\> is the IP Address of the seed
        - \<seed_port\> is the Port Number of the seed
        - \<verbose\> is 1 if you want to log all the messages else 0

        Make sure that the seeds run match the config.txt file

    3. Start the peers in the network by running peer.py file with the given IP and port <br>
        `python3 peer.py <peer_IP> <peer_port> <verbose>` where 
        - \<peer_ip\> is the IP Address of the peer
        - \<peer_port\> is the Port Number of the peer
        - \<verbose\> is 1 if you want to log all the messages else 0

    4. To test the presence of a malicious peer in the network run <br>
        `python3 malicious_peer.py <peer_IP> <peer_port> <verbose>` where
        - \<peer_ip\> is the IP Address of the peer
        - \<peer_port\> is the Port Number of the peer
        - \<verbose\> is 1 if you want to log all the messages else 0