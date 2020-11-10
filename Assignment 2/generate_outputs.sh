#!/bin/bash

#Start the seed node
python3 seed.py --IP 127.0.0.1 --verbose --no_print --outdir outfiles/seed --port 2346 &

for nflood in 1 2 3
do
    for iat in 2 4 8 16 32
    do
    echo "Inter Arrival Time ${iat}s with $(( nflood*10 ))% nodes flooded"
    python3 blockchain.py --IP 127.0.0.1 --verbose --inter_arrival_time $iat --hash_fraction 0.074  --outdir outfiles/ia_${iat}_pf_${nflood} --port 1235 --network_delay 1 --terminate_after 610 --no_print &
    python3 blockchain.py --IP 127.0.0.1 --verbose --inter_arrival_time $iat --hash_fraction 0.074  --outdir outfiles/ia_${iat}_pf_${nflood} --port 2340 --network_delay 1 --terminate_after 610 --no_print &
    python3 blockchain.py --IP 127.0.0.1 --verbose --inter_arrival_time $iat --hash_fraction 0.074  --outdir outfiles/ia_${iat}_pf_${nflood} --port 3453 --network_delay 1 --terminate_after 610 --no_print &
    python3 blockchain.py --IP 127.0.0.1 --verbose --inter_arrival_time $iat --hash_fraction 0.074  --outdir outfiles/ia_${iat}_pf_${nflood} --port 4565 --network_delay 1 --terminate_after 610 --no_print &
    python3 blockchain.py --IP 127.0.0.1 --verbose --inter_arrival_time $iat --hash_fraction 0.074  --outdir outfiles/ia_${iat}_pf_${nflood} --port 5676 --network_delay 1 --terminate_after 610 --no_print &
    python3 blockchain.py --IP 127.0.0.1 --verbose --inter_arrival_time $iat --hash_fraction 0.074  --outdir outfiles/ia_${iat}_pf_${nflood} --port 6782 --network_delay 1 --terminate_after 610 --no_print &
    python3 blockchain.py --IP 127.0.0.1 --verbose --inter_arrival_time $iat --hash_fraction 0.074  --outdir outfiles/ia_${iat}_pf_${nflood} --port 7891 --network_delay 1 --terminate_after 610 --no_print &
    python3 blockchain.py --IP 127.0.0.1 --verbose --inter_arrival_time $iat --hash_fraction 0.074  --outdir outfiles/ia_${iat}_pf_${nflood} --port 8902 --network_delay 1 --terminate_after 610 --no_print &
    python3 blockchain.py --IP 127.0.0.1 --verbose --inter_arrival_time $iat --hash_fraction 0.078  --outdir outfiles/ia_${iat}_pf_${nflood} --port 9013 --network_delay 1 --terminate_after 610 --no_print &
    python3 adversary.py --IP 127.0.0.1 --verbose --inter_arrival_time $iat --hash_fraction 0.33  --outdir outfiles/ia_${iat}_pf_${nflood} --port 8990 --network_delay 1 --terminate_after 610 --no_print --num_flood $nflood --flood_every 0.5 &

    sleep 800

    done
done
