import time
from threading import Thread, Event

from scapy.all import sendp
from scapy.layers.inet import IP, ICMP
from scapy.layers.l2 import ARP

from router.pwospf import PWOSPF, Hello
from switch.async_sniff import sniff
from switch.cpu_metadata import CPUMetadata

ARP_OP_REQUEST = 0x0001
ARP_OP_RESPONSE = 0x0002

HELLO_TYPE = 0x01
LSU_TYPE = 0x04


# każdy interfejs rozsyłamy lsuad - lsuadvertisement
# https://github.com/AWoLnik/router/blob/master/router.p4app/pwospf.py

class MacLearningController(Thread):
    def __init__(self, sw, router_ip, area_id, start_wait=0.3):
        super(MacLearningController, self).__init__()
        self.sw = sw
        self.router_ip = router_ip
        self.area_id = area_id
        self.start_wait = start_wait  # time to wait for the controller to be listening
        self.iface = sw.intfs[1].name
        self.port_for_mac = {}
        self.stop_event = Event()

    def add_mac_address(self, mac, port):
        if mac in self.port_for_mac: return

        self.sw.insertTableEntry(table_name='MyIngress.fwd_l2',
                                 match_fields={'hdr.ethernet.dstAddr': [mac]},
                                 action_name='MyIngress.set_egr',
                                 action_params={'port': port})
        self.port_for_mac[mac] = port

    def handle_icmp_echo_request(self, pkt):
        # Creating an ICMP Echo reply
        icmp_reply = IP(dst=pkt[IP].src) / ICMP(type=0, code=0) / pkt[IP]

        # Sending the reply back to the source host
        self.send(icmp_reply)

    def handle_unreachable_host(self, pkt):
        # Creating an ICMP host unreachable packet (ICMP type 3, code 1)
        icmp_unreachable = IP(dst=pkt[IP].src) / ICMP(type=3, code=1)

        # Sending the ICMP host unreachable packet
        self.send(icmp_unreachable)

    def handle_arp_response(self, pkt):
        self.add_mac_address(pkt[ARP].hwsrc, pkt[CPUMetadata].srcPort)
        self.send(pkt)

    def handle_arp_request(self, pkt):
        # check in routing table
        self.add_mac_address(pkt[ARP].hwsrc, pkt[CPUMetadata].srcPort)
        # self.send(pkt)

    def handle_direct_to_router(self, pkt):
        if PWOSPF in pkt:
            if pkt[PWOSPF].version != 2: return
            # TODO: verify checksum
            if pkt[PWOSPF].areaID != self.area_id: return
            if pkt[PWOSPF].auType != 0: return
            if pkt[PWOSPF].auth != 0: return
            routerID = pkt[PWOSPF].routerID
            if Hello in pkt:
                intf = None
                # for i in self.intfs:
                #     if i.port == pkt[CPUMetadata].srcPort:
                #         intf = i
                # if pkt[Hello].netmask != intf.mask: return
            #     if pkt[Hello].helloint != intf.helloint: return
            #
            #     intfIP = pkt[IP].src
            #     if intf.hasNeighbor(routerID, intfIP):
            #         intf.setNeighborUpdateTime(routerID, intfIP, time.time())
            #     else:
            #         intf.addNeighbor(routerID, intfIP)
            #
            # if LSU in pkt:
            #     if routerID == self.routerID: return
            pass
            # TODO o co chodzi z pakietami przesyłanymi bezpośrednio do routera
            # TODO Każdy dodatkowy protokół ma mieć swój plik, w naszym wypadku PW_OSPF
            # Patrzymy czy hello message czy to drugie i tu przerabiamy

    def handle_packet(self, pkt):
        # pkt.show2()
        assert CPUMetadata in pkt, "Should only receive packets from switch with special header"

        # Ignore packets that the CPU sends:
        if pkt[CPUMetadata].fromCpu == 1: return

        if ARP in pkt:
            if pkt[ARP].op == ARP_OP_REQUEST:
                self.handle_arp_request(pkt)
            elif pkt[ARP].op == ARP_OP_RESPONSE:
                self.handle_arp_response(pkt)
        elif ICMP in pkt:
            if pkt[ICMP].type == 8:  # ICMP Echo Request
                self.handle_icmp_echo_request(pkt)
        else:
            if IP in pkt:
                self.handle_direct_to_router(pkt)
            else:
                self.handle_unreachable_host(pkt)

    def send(self, *args, **override_kwargs):
        pkt = args[0]
        assert CPUMetadata in pkt, "Controller must send packets with special header"
        pkt[CPUMetadata].fromCpu = 1
        kwargs = dict(iface=self.iface, verbose=False)
        kwargs.update(override_kwargs)
        sendp(*args, **kwargs)

    def run(self):
        sniff(iface=self.iface, prn=self.handle_packet, stop_event=self.stop_event)

    def start(self, *args, **kwargs):
        super(MacLearningController, self).start(*args, **kwargs)
        time.sleep(self.start_wait)

    def join(self, *args, **kwargs):
        self.stop_event.set()
        super(MacLearningController, self).join(*args, **kwargs)
