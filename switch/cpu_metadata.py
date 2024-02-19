from scapy.fields import ByteField, ShortField
from scapy.layers.l2 import Ether
from scapy.packet import Packet, bind_layers

TYPE_CPU_METADATA = 0x080a


class CPUMetadata(Packet):
    name = "CPUMetadata"
    fields_desc = [ByteField("fromCpu", 0),
                   ShortField("origEtherType", None),
                   ShortField("srcPort", None)]
# srcPort a port on which the packet was originally sent to data plane


bind_layers(Ether, CPUMetadata, type=TYPE_CPU_METADATA)
