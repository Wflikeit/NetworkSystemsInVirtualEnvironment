set -e

if ! [ -f ./router.p4 ]; then
  echo "File router.p4 not found in running directory"
  exit 1
fi

if ! [ -f /root/bmv2/bin/router.json ] || ! [ -f /root/bmv2/bin/router.p4info.txt ]; then
  sudo p4c-bm2-ss -I /usr/share/p4c/p4include --std p4-16 --p4runtime-files /root/bmv2/bin/router.p4info.txt -o /root/bmv2/bin/router.json router.p4
fi

if ! [ -f ./$1 ]; then
  echo "File $1 not found in running directory"
  exit 1
fi
config=$(<$1)

run_simple_switch_grpc="simple_switch_grpc -i 1@eth0"

i=2
# Read JSON data and process each entry
echo "$config" | jq -c '.[]' | { while read -r entry; do
	# Extract IP, MASK, and MAC
	ip=$(echo "$entry" | jq -r '.IP')
	mask=$(echo "$entry" | jq -r '.MASK')
	mac=$(echo "$entry" | jq -r '.MAC')

    # Create interface name based on MAC address
	iface_name="enx${mac//:/}"
	if ip link show ${iface_name} > /dec/null 2>&1; then
		sudo ifconfig ${iface_name} up
	else
		echo "There is no such interface with name: ${iface_name}"
	fi
	
    # Add interface to simple_switch_grpc command parameters
	run_simple_switch_grpc="${run_simple_switch_grpc} -i ${i}@${iface_name}"
	i=$((i+1))

    # Set UP interface
	sudo ifconfig ${iface_name} up
	
done

if ip link show eth0 > /dev/null 2>&1; then
	sudo ip link delete eth0
	sudo ip link add eth0 type dummy
	sudo ifconfig eth0 up
else
	sudo ip link add eth0 type dummy
	sudo ifconfig eth0 up
fi
if ! [ -d ./logs ]; then
	mkdir logs
fi

run_simple_switch_grpc="sudo screen -L -Logfile ./logs/switch_screen.txt -dmS switch ${run_simple_switch_grpc} /root/bmv2/bin/router.json --log-console --pcap ./logs/ -- --grpc-server-addr 127.0.0.1:50051"
if $run_simple_switch_grpc > /dev/null 2>&1; then
	echo "Successfully initialized grpc switch"
else
	echo "Failed to initialize grpc switch"
	exit 1
fi
}

if ! [ -f ./main_pi_router.py ]; then
  echo "File main_pi_router.py not found in running directory"
  sudo screen -X -S switch quit
  exit 1
fi

if sudo screen -L -Logfile ./logs/controller_screen.txt -dmS controller python3 main_pi_router.py --p4info /root/bmv2/bin/router.p4info.txt --bmv2-json /root/bmv2/bin/router.json --intfs-config $1 > /dev/null 2>&1;then
	echo "Successfully initialized controller"
else
	echo "Failed to initialize controller"
	sudo screen -X -S switch quit
	exit 1
fi
