import PodSixNet.Channel
import PodSixNet.Server
from time import sleep

class ClientChannel(PodSixNet.Channel.Channel):
    def Network(self, data):
        print data


class myGameServer(PodSixNet.Server.Server):
    channelClass = ClientChannel

    def Connected(self, channel, addr):
        print 'new connection:', channel


print "STARTING SERVER ON LOCALHOST"
the_server = myGameServer()
while True:
    the_server.Pump()
    sleep(0.01)