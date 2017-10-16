#!/bin/bash
toilet "magicmirror" | lolcat --freq 0.25   
printf '%*s\n' "${COLUMNS:-$(tput cols)}" '' | tr ' ' -
bold=$(tput bold)
normal=$(tput sgr0)
echo "${bold}Config Details${normal}"
ip route get 1 | awk '{print "IP Address: " $NF;exit}'
printf '%*s\n' "${COLUMNS:-$(tput cols)}" '' | tr ' ' -
echo ""

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

# Run all concurrently. Killing processes on ctrl+c
python webserver.py &
python websocket_server.py &
python interaction_logger.py &
python image_processor.py &
wait