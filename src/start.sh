#!/bin/bash
# Run both concurrently. Killing both on ctrl+c

intexit() {
    # Kill all subprocesses (all processes in the current process group)
    kill -HUP -$$
}

hupexit() {
    # HUP'd (probably by intexit)
    echo
    echo "Interrupted"
    exit
}

trap hupexit HUP
trap intexit INT

python webserver.py &
python websocket_server.py &
python interaction_logger.py &
wait