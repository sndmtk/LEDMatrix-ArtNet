import numpy as np

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor

class ArtNet(DatagramProtocol):
    
    def __init__(self):
        self.buffer = np.zeros(12288)
        self.last_sequence = [-1, -1]


    def datagramReceived(self, data, addr):
        #print "received {!r} from {}".format(data,addr)
        if data[0:8] == 'Art-Net\x00':
            rawbytes = map(ord, data)
            opcode = rawbytes[8] + (rawbytes[9] << 8)
            protocolVersion = (rawbytes[10] << 8) + rawbytes[11] 
            if ((opcode == 0x5000) and (protocolVersion >= 14)):
                sequence = rawbytes[12]
                physical = rawbytes[13]
                sub_net = (rawbytes[14] & 0xF0) >> 4
                universe = rawbytes[14] & 0x0F
                net = rawbytes[15]
                data_length = (rawbytes[16] << 8 ) + rawbytes[17]
                rgbdata = rawbytes[18:(data_length+18)]

                if self.last_sequence[net] != sequence:
                    # send data
                    print 'send data', net

                    # set sequence
                    self.last_sequence[net] = sequence
                
                # store data
                self.buffer[512*(universe+16*net):512*(universe+16*net+1)] = rgbdata

try:
    reactor.listenUDP(6454, ArtNet())
    reactor.run()
except KeyboardInterrupt:
    reactor.stop()
