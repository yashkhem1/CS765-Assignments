#!/bin/bash

#Start the seed node
python3 seed.py --IP 127.0.0.1 --verbose --no_print --outdir outfiles_cont/seed --port 2346 &

for nflood in 1 2 3
do
    for iat in 2 6 10 14 18
    do
    echo "Inter Arrival Time ${iat}s with $(( nflood*10 ))% nodes flooded"
    python3 blockchain.py --IP 127.0.0.1 --inter_arrival_time $iat --hash_fraction 0.074  --outdir outfiles_cont/ia_${iat}_pf_${nflood} --port 1235 --seed 1 --network_delay 2 --terminate_after 600 --no_print &
    sleep 1
    python3 blockchain.py --IP 127.0.0.1 --inter_arrival_time $iat --hash_fraction 0.074  --outdir outfiles_cont/ia_${iat}_pf_${nflood} --port 2340 --seed 2 --network_delay 2 --terminate_after 600 --no_print &
    sleep 1
    python3 blockchain.py --IP 127.0.0.1 --inter_arrival_time $iat --hash_fraction 0.074  --outdir outfiles_cont/ia_${iat}_pf_${nflood} --port 3453 --seed 3 --network_delay 2 --terminate_after 600 --no_print &
    sleep 1
    python3 blockchain.py --IP 127.0.0.1 --inter_arrival_time $iat --hash_fraction 0.074  --outdir outfiles_cont/ia_${iat}_pf_${nflood} --port 4565 --seed 4 --network_delay 2 --terminate_after 600 --no_print &
    sleep 1
    python3 blockchain.py --IP 127.0.0.1 --inter_arrival_time $iat --hash_fraction 0.074  --outdir outfiles_cont/ia_${iat}_pf_${nflood} --port 5676 --seed 5 --network_delay 2 --terminate_after 600 --no_print &
    sleep 1
    python3 blockchain.py --IP 127.0.0.1 --inter_arrival_time $iat --hash_fraction 0.074  --outdir outfiles_cont/ia_${iat}_pf_${nflood} --port 6782 --seed 6 --network_delay 2 --terminate_after 600 --no_print &
    sleep 1
    python3 blockchain.py --IP 127.0.0.1 --inter_arrival_time $iat --hash_fraction 0.074  --outdir outfiles_cont/ia_${iat}_pf_${nflood} --port 7891 --seed 7 --network_delay 2 --terminate_after 600 --no_print &
    sleep 1
    python3 blockchain.py --IP 127.0.0.1 --inter_arrival_time $iat --hash_fraction 0.074  --outdir outfiles_cont/ia_${iat}_pf_${nflood} --port 8902 --seed 8 --network_delay 2 --terminate_after 600 --no_print &
    sleep 1
    python3 blockchain.py --IP 127.0.0.1 --inter_arrival_time $iat --hash_fraction 0.078  --outdir outfiles_cont/ia_${iat}_pf_${nflood} --port 9013 --seed 9 --network_delay 2 --terminate_after 600 --no_print &
    sleep 1
    python3 adversary.py --IP 127.0.0.1 --inter_arrival_time $iat --hash_fraction 0.33  --outdir outfiles_cont/ia_${iat}_pf_${nflood} --port 8990 --seed 10 --network_delay 2 --terminate_after 600 --no_print --num_flood $nflood --flood_every 0.001 &

    sleep 700

    done
done
