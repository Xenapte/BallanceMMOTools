#! /bin/bash
function ctrlc_exit () {
	echo -e "\n------------\nStopping..."
	for i in $loop_num; do screen -S bmmo$i -p 0 -X stuff "stop^M" && sleep 0.2; done
	exit 0
}
function translate () {
	for (( ; ; ))
	do
		for i in $loop_num; do screen -S bmmo$i -p 0 -X stuff "translate^M"; done
		sleep $1
	done
}
set -o braceexpand
loop_num=$(seq -f "%02.0f" -s " " $1)
trap "ctrlc_exit" 2
echo Spawning $1 clients...
for i in $loop_num; do sleep 0.2 && screen -dmS bmmo$i ./BallanceMMOMockClient -n f$i; done
echo Success. To execute additional commands, type this in your regular shell:
echo for i in \$\(seq -f %02.0f $1\)\; do screen -S bmmo\$i -p 0 -X stuff \"\{cmd\}^M\"\; done
echo ------------
translate $2 &
for (( ; ; ))
do
	read -p "Client id to teleport to: " client_id
	for i in $loop_num; do screen -S bmmo$i -p 0 -X stuff "teleport $client_id^M"; done
done

