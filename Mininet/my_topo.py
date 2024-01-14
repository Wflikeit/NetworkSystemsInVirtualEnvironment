from mininet.cli import CLI
from mininet.net import Mininet
from mininet.node import Node, Switch, OVSSwitch
from mininet.topo import Topo


class LinuxSwitch(OVSSwitch):
    def __init__(self, name, **params):
        super(LinuxSwitch, self).__init__(name, **params)
        self.failMode = 'standalone'

    def start(self, controller=None):
        super(LinuxSwitch, self).start(controllers=[])


routing_table = {
    'r1': [['20.0.0.0/24', '192.168.1.2', 'r1-eth1'],
           ['default', '192.168.2.1', 'r1-eth2']],
    'r2': [['default', '192.168.3.2', 'r2-eth2'],
           ['102.168.0.0/24', '192.168.1.1', 'r2-eth1'],
           ['192.168.2.0/24', '192.168.3.1', 'r2-eth2'], ],
    'r3': [['20.0.0.0/24', '192.168.3.1', 'r3-eth1'],
           ['102.168.0.0/24', '192.168.2.2', 'r3-eth0']]
}


class LinuxRouter(Switch):
    """
    The LinuxRouter class represents a simple router based on the Linux system.

    Parameters:
        name (str): Router name.
        **params: Additional parameters passed to the parent Node class.

    Attributes:
        failMode (str): Router fail mode, default is 'standalone'.
        routing_table (dict): Router's routing table, initialized with an external table.

    Methods:
        config(**params): Configures the router by setting 'net.ipv4.ip_forward' to 1.
        terminate(): Shuts down the router by setting 'net.ipv4.ip_forward' to 0.
        setARP(ip, mac): Sets an ARP entry for a specified IP and MAC address.
        defaultIntf(): Returns the default interface of the router.
        addRoute(entry): Adds a route to the router's routing table.
        start(controllers): Starts the router by adding routes defined in the routing table.

    """

    def __init__(self, name, **params):
        """
        Initializes an object of the LinuxRouter class.

        Parameters:
            name (str): Router name.
            **params: Additional parameters passed to the parent Node class.
        """
        Node.__init__(self, name, **params)
        self.failMode = 'standalone'
        self.routing_table = routing_table[self.name]

    def config(self, **params):
        """
        Configures the router by setting 'net.ipv4.ip_forward' to 1.

        Parameters:
            **params: Additional parameters passed to the parent Node class.
        """
        super(LinuxRouter, self).config(**params)
        self.cmd('sysctl net.ipv4.ip_forward=1')

    def terminate(self):
        """
        Shuts down the router by setting 'net.ipv4.ip_forward' to 0.
        """
        self.cmd('sysctl net.ipv4.ip_forward=0')
        super(LinuxRouter, self).terminate()

    def setARP(self, ip, mac):
        """
        Sets an ARP entry for a specified IP and MAC address.

        Parameters:
            ip (str): IP address.
            mac (str): MAC address.
        """
        super(LinuxRouter, self).setARP(ip, mac)

    def defaultIntf(self):
        """
        Returns the default interface of the router.

        Returns:
            Intf: Default interface of the router.
        """
        return Node.defaultIntf(self)

    def addRoute(self, entry):
        """
        Adds a route to the router's routing table.

        Parameters:
            entry (tuple): Tuple containing information about the route (dst, via, dev).
        """
        dev = 'dev ' + entry[2] if len(entry) == 3 else ''
        dst = entry[0]
        via = entry[1]
        self.cmd('ip r add ', dst, ' via ', via, dev)

    def start(self, controllers):
        """
        Starts the router by adding routes defined in the routing table.

        Parameters:
            controllers: List of controllers.
        """
        r_name = self.name
        for entry in routing_table[r_name]:
            self.addRoute(entry)
        self.cmd('sysctl net.ipv4.ip_forward=1')


class MyTopo(Topo):
    def build(self, **_opts):
        r1 = self.addSwitch('r1', cls=LinuxRouter, inNamespace=True, ip='102.168.0.1/24')
        r2 = self.addSwitch('r2', cls=LinuxRouter, inNamespace=True, ip='20.0.0.1/24')
        r3 = self.addSwitch('r3', cls=LinuxRouter, inNamespace=True, ip='192.168.2.1/24')

        s1 = self.addSwitch('s1', cls=LinuxSwitch, inNamespace=False)

        h1 = self.addHost('h1',
                          ip='20.0.0.2/24',
                          mac='00:00:00:00:01:01',
                          defaultRoute='via 20.0.0.1')
        h2 = self.addHost('h2',
                          ip='102.168.0.2/24',
                          mac='00:00:00:00:00:01',
                          defaultRoute='via 102.168.0.1')
        h3 = self.addHost('h3',
                          ip='102.168.0.3/24',
                          mac='00:00:00:00:00:02',
                          defaultRoute='via 102.168.0.1')

        self.addLink(s1, h3)
        self.addLink(s1, h2)
        self.addLink(r2, h1,
                     intfName1='r2-eth0',
                     params1={'ip': '20.0.0.1/24'})

        self.addLink(r1, s1,
                     intfName1='r1-eth0',
                     params1={'ip': '102.168.0.1/24'})
        self.addLink(r1, r2,
                     intfName1='r1-eth1',
                     intfName2='r2-eth1',
                     params1={'ip': '192.168.1.1/24'},
                     params2={'ip': '192.168.1.2/24'})
        self.addLink(r1, r3,
                     intfName1='r1-eth2',
                     intfName2='r3-eth0',
                     params1={'ip': '192.168.2.2/24'},
                     params2={'ip': '192.168.2.1/24'})
        self.addLink(r2, r3,
                     intfName1='r2-eth2',
                     intfName2='r3-eth1',
                     params1={'ip': '192.168.3.1/24'},
                     params2={'ip': '192.168.3.2/24'})


net = Mininet(topo=MyTopo(), controller=None, autoStaticArp=False)
net.start()

CLI(net)
net.stop()
