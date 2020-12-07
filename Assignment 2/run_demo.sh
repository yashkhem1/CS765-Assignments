#!/bin/bash

#Start the seed
"echo Starting Seed"
gnome-terminal -- bash -c "python3 seed.py --IP 127.0.0.1 --verbose  --outdir $2 --port 2346; exec bash"

sleep 3
#Start the nodes
echo "Starting node 1"
gnome-terminal -- bash -c "python3 blockchain.py --IP 127.0.0.1 --verbose --inter_arrival_time 4 --hash_fraction 0.33  --outdir $2 --port 1235 --draw --terminate_after $3; exec bash"

sleep 6
echo "Starting node 2"
gnome-terminal -- bash -c "python3 blockchain.py --IP 127.0.0.1 --verbose --inter_arrival_time 4 --hash_fraction 0.33  --outdir $2 --port 1236 --draw --terminate_after $3; exec bash"

sleep 6
if [ $1 = "adversary" ]
then
    echo "Starting adversarial node"
    gnome-terminal -- bash -c "python3 adversary.py --IP 127.0.0.1 --verbose --inter_arrival_time 4 --hash_fraction 0.33  --outdir $2 --port 1237  --num_flood 1 --flood_every 0.5 --draw --terminate_after $3; exec bash"

else
    echo "Starting node 3"
    gnome-terminal -- bash -c "python3 blockchain.py --IP 127.0.0.1 --verbose --inter_arrival_time 4 --hash_fraction 0.33  --outdir $2 --port 1237 --draw --terminate_after $3; exec bash"
fi

