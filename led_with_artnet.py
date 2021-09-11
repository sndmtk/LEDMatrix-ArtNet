import time
import numpy as np
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor

import spidev
import RPi.GPIO as GPIO
SS = 8
DC = 12

class ArtNet(DatagramProtocol):

    def __init__(self):
        self.flag = 0
        self.buffer = np.zeros(12288)
        self.backbuffer1 = np.zeros(12288)
        self.backbuffer2 = np.zeros(12288)
        self.last_sequence = [-1, -1]
        self.spi = spidev.SpiDev()
        self.spi.open(0,0)
        self.spi.mode = 0
        self.spi.max_speed_hz = 8000000

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(SS,GPIO.OUT)
        GPIO.setup(DC,GPIO.OUT)

        GPIO.output(SS,True)
        GPIO.output(DC,False)
        time.sleep(0.01)

    def store(self):
        self.backbuffer2 = self.backbuffer1
        self.backbuffer1 = self.buffer.astype(int)

    def send(self):
        GPIO.output(DC, True)
        time.sleep(0.000001)
        GPIO.output(DC, False)
        time.sleep(0.000001)

        GPIO.output(SS, False)
        self.spi.xfer(self.buffer.astype(int))
        GPIO.output(SS, True)

    def datagramReceived(self, data, addr):
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

                # store data
                self.buffer[512*(universe+16*net):512*(universe+16*net+1)] = rgbdata

                if self.last_sequence[net] != sequence:
                    self.send()
                
                self.last_sequence[net] = sequence



if __name__ == '__main__':
    artnet = ArtNet()
    try:
        reactor.listenUDP(6454, artnet)
        reactor.run()

    except KeyboardInterrupt:
        reactor.stop()
        GPIO.cleanup()
        artnet.spi.close()
