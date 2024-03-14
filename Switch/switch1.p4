#ifdef _SWITCH_P4_
#define _SWITCH_P4_


#include <core.p4>
#include <v1model.p4>

typedef bit<9> egressSpec_t;
typedef bit<9> port_t;
typedef bit<4> PortID;
typedef bit<48> MacAddress_t;
typedef bit<32> IPv4Addrress_t;
typedef bit<16> MulticastGroup_t;

#port constans

const port_t CpuPort = 0x1;

const bit<16> ArpRequest = 0x0001;  #czemu tak?
const bit<16> ArpReply = 0x0002;   #czemu tak? chyba chodzi o określenie typu wiadomosci ARp jak jest 0x002 czyli 2 to jest reply jak 0x001 czyli 1 to request

const bit<16> TypeArp = 0x0806;
const bit<16> CpuMetaDataType = 0x080a;

header Ethernet_t{
    MacAddress_t SourceAddress;
    MacAddress_t DestinationAddress;
    bit<16> ethertype;
    }

header ARP_t{
    bit<8> HardwareAddressLength;
    bit<8> ProtocolAddressLength;
    bit<16> HardwareType;
    bit<16> Protocoltype;
    bit<16> Opcode;

header CpuMetaData_t{
    bit<8> FromCpu;
    bit<16> SourcePort;
    bit<16> OriginEthertype;
    }


#nwm czy nie powinno być tak jak w tym switchu z yale ze jest załozenie ze hardware to eth a protokul to ip

    MacAddress_t SenderHardwareAddress;
    MacAddress_t TargetHardwareAddress;
    IPv4Address_t SenderprotocolAddress;
    IPv4Address_t TargetProtocolAddress;
    }

struct headers{
    Ethernet_t ethernet;
    CpuMetaData_t cpu_metadata;
    ARP_t arp;
    }
    struct metadata{}


parser Parser(packet_in packet,out_of_headers hdr,inout standard_metadata_t standard_metadata)
    { state start {
        transition parse_ethernet; }

    state parse_ethernet{
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType)
            {CpuMetaDataType: parse_cpu_metadata;
                TypeArp: parse_arp;
            default: accept; }
            }


    state parse cpu_metadata{
    packet.extract(hdr.cpu_metadata);
    transition select (hdr.cpu_metadata.OriginEthertype){
    TypeArp: parse_arp;
    default: accept;}
    }

    state parse_arp{
    packet.extract(hdr.arp);
    transition select(hdr.arp){
    default: accept;}
    }

    control VerifyChecksum(inout headers hdr, inout metadata metad){
        apply() }

    control Ingress(inout headers hdr, inout standard_metadata_t standard_metadata, inout metadata meta) {

    action drop() {
        mark_to_drop(standard_metadata);
         }
    action mac_forward(egressSpec_t eport){
        standard_metadata.egress_spec = eport;
        }

    action set_multicast_group_id(multicastgrp_t mgrpid) {
        standard_metadata.multicastgrp = mgrpid;
        }

    table MacLookUp{
        key = {
        hdr.ethernet.DestinationAddress : exact;
        }
    actions = {
        mac_forward;
        drop;
        }
    size = 1024;
    defaction = drop;
    }
    apply {
    if(hdr.ethernet.isValid())
        MacLookUp.apply();
        }
    }

    control Egress(inout headers hdr, inout standard_metadata_t standard_metadata, inout metadata meta){
        action drop(){
            mark_to_drop(standard_metadata);
            }
        apply{
            if(standard_metadata.egress_port == standard_metadata.ingress_port)
                drop();
        }
      }

    control ComputeChecksum(inout headers hdr, inout metadata meta){
        apply{
        }
       }

    control Deparser(packet_out packet, in headers hdr){
        apply{
            packet.emit(hdr.ethernet);
            packet.emit(hdr.arp);
            packet.emit(hdr.cpu_metadata);
        }
    }

V1Switch(
Parser(),
VerifyChecksum(),
Ingress(),
Egress(),
ComputeChecksum(),
Deparser(), )
main;
#endif