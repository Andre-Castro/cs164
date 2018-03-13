from mininet.topo import Topo

class MyFirstTopo( Topo ):
	#Simple topology example.
	def __init__(self):
		#Inti topology
		Topo.__init__(self)
		#Add hosts and switches
		b1 = self.addHost( 'b1', ip = '10.0.0.1/24' )
		b2 = self.addHost( 'b2', ip = '10.0.0.2/24' )
		b3 = self.addHost( 'b3', ip = '10.0.0.3/24' )
		b4 = self.addHost( 'b4', ip = '10.0.0.4/24' )

		centralSwitch = self.addSwitch( 's1' )

		#Add links
		self.addLink( b1, centralSwitch )
		self.addLink( b2, centralSwitch )
		self.addLink( b3, centralSwitch )
		self.addLink( b4, centralSwitch )

topos = { 'myfirsttopo': (lambda: MyFirstTopo() ) }
