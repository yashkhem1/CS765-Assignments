# Assignment 2
## Implementation of Blockchain over the P2P network
### Team : Yash Khemchandani (170050025), Devansh Garg(170050029), Ajay Sheoran(170050042)

* ### <b>Source code files</b>
    - seed.py
        - Contains the code for the seeds in the P2P network
        - Uses TCP sockets and implemented using socket and select modules in Python

    - peer.py
        - Contains the code for peers in the P2P network
        - Uses TCP sockets and implemented using socket module in Python

    - config.txt
        - Contains the IP and port information for the seeds in the P2P network
        - Used by the incoming peers to connect to the seeds

    - blockchain.py
        - Contains the code for Blockchain peer in the P2P network
        - Mines the block and adds valid incoming blocks to the local blockchain

    - adversary.py
        - Contains the code for Adversary peer in the P2P network
        - Includes all the functionality of the Blockchain peer
        - Floods a set of target peers with invalid blocks to prevent them from mining

* ### <b>Sample output directories</b>
    
    - outfile-plots
        - Contains the output files for the experiments done to generate the plots, in which the P2P network had 10 nodes (including 1 adversary node) and each experiment was run for 20 minutes
        - A subdirectory of the format ia\_<b>x</b>\_pf\_<b>y</b> contains the output of the experiment where inter-arrival time is <b>x</b> seconds and number of nodes flooded in the network is <b>y</b>
        - _blockchain*.txt_ files contain the final state of the blockchain, with the leftmost block header in each line being part of the main chain
        - _outputpeer*.txt_ files contain the peer log and  _outputseed*.txt_ files contain the seed log

    - trees_outfiles_adversary
        - Contains the output files for the network containing 2 honest nodes and 1 malicious node run for 10 minutes. This directory also contains the blockchain tree diagrams at every node
        - _*.png_ files have the spiral tree structure and _*.dot_ files have the heirarchial tree structure  in a dot format
        - To convert _dot_ files to _png_ files simply run, <br>
        `dot -Tpng input.dot -o output.png` <br>
        _*.dot.png_ files are the dot files which have been converted to png format   

    - trees_outfiles_normal
        - Contains the output files for the network containing 3 honest nodes run for 10 minutes

* ### <b>Runnable Scripts</b>
    - In order to run the experiments for different inter arrival times and percentage nodes flooded, run `./generate_outputs.sh`.    Since each experiment runs for 20 minutes and there are 15 such experiments, this script will take around 3.5 hrs.

    - A demo run with 3 honest nodes or (2 honest nodes and 1 malicious node) can also be done by running <br>
        `./run_demo.sh <normal/adversary> <outdir> <time> <start_port> <flood_every>` where
        - \<normal/adversary\> is normal for 3 honest nodes or adversary for 2 honest nodes and 1 malicious node
        - \<outdir\> is the directory where the output files will be saved
        - \<time\> is the time in seconds for the simulation will run
        - \<start_port\> is the starting port number. The 3 nodes will have 3 consecutive port numbers starting from the starting_port
        - \<flood_every\> is the time interval between successive invalid blocks sent by the adversary

    - For generating the plots of mining power utilization and fraction of main chain blocks mined by the adversary, run <br>
        `python3 generate_plots.py <outdir> <adversary_port>` where
        - \<outdir\> is the directory containing the output files
        - \<adversary_port\> is the port number for the adversary