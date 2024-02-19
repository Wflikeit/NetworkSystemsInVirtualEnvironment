#
# if __name__ == '__main__':
#     sw.addMulticastGroup(mgid=bcast_mgid, ports=range(2, N + 1))
#
#     # Send MAC bcast packets to the bcast multicast group
#     sw.insertTableEntry(table_name='MyIngress.fwd_l2',
#                         match_fields={'hdr.ethernet.dstAddr': ["ff:ff:ff:ff:ff:ff"]},
#                         action_name='MyIngress.set_mgid',
#                         action_params={'mgid': bcast_mgid})
#
#     # Start the MAC learning controller
#     cpu = MacLearningController(sw)
#     cpu.start()
# TODO uncomment thi sto config file and add multicast group