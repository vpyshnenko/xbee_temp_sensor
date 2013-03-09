#!/usr/bin/python

import logging
import serial

logger = logging.getLogger('default')

# Sample packet:
# 7e 0 e 83 56 78 3f 0 1 7 0 1 0 3 ff 3 ff 62 
# 

# I/O data packet
#
#  header:
#
# Total number of samples | na A5 A4 A3 A2 A1 A0 D8 | D7 D6 D5 D4 D3 D2 D1 D0 |
#
# sample data follows the header:
#
#   DIO line data first (if enabled)  |         ADC line data
#   x x x x x x x 8 | 7 6 5 4 3 2 1 0 | ADCn MSB       | ADCn LSB

# in the example above:
#
#  cmd   -- 83    (16 bit I/O)
#  56 78 -- address
#  3f    -- RSSI
#   0    -- options
# next follows I/O data packet (because cmd was 83)
#   1    -- num. of samples
#   7    -- first byte of channel spec, A1=1 A0=1 D8=1
#   0    -- second byte of channel spec, all other channels are off
#   1    -- first sample byte, D8=1    -- only if any of D channels enabled
#   0    -- second sample byte         -- only if any of D channels enabled
#   3    -- ADC0 MSB
#  ff    -- ADC0 LSB
#   3    -- ADC1 MSB
#  ff    -- ADC1 LSB

class SerialIOPacket(object):
    def __init__(self):
        self.api_16_bit_adc = 0x83
        self.api_64_bit_adc = 0x82

        self.cmd = None
        self.packet_size = 0  # includes everything from start byte to crc
        self.length = 0       # payload part of the packet
        self.frame = []
        self.address = ''
        self.rssi = 0
        self.options = ''
        self.num_samples = 0
        self.a_channels_enabled = []
        self.d_channels_enabled = []
        self.have_d_channels = False
        self.num_a_channels = 0
        self.a_channels_data = []
        self.d_channels_data = []

    def decode_channels(self, channel_ind_1, channel_ind_2):
        self.a_channels_enabled = [False for x in range(0,8)]
        self.d_channels_enabled = [False for x in range(0,9)]

        for bit in range(1, 7):
            self.a_channels_enabled[bit-1] = bool(channel_ind_1 & 1 << bit)

        self.d_channels_enabled[8] = bool(channel_ind_1 & 1)

        for bit in range(0, 7):
            self.d_channels_enabled[bit] = bool(channel_ind_2 & 1 << bit)

        for i in range(0, len(self.d_channels_enabled)):
            self.have_d_channels = self.have_d_channels or self.d_channels_enabled[i]

        for i in range(0, len(self.a_channels_enabled)):
            self.num_a_channels += int(self.a_channels_enabled[i])

    def d_data(self, sample_1, sample_2):
        self.d_channels_data[8] = bool(sample_1 & 1)

        for bit in range(0, 8):
            self.d_channels_data[bit] = bool(sample_2 & 1 << bit)
    
    def a_data(self, msb, lsb):
        # ADC is 10 bit
        return (msb & 0x3) * 256 + lsb

    def decode_packet(self, frame, length):
        """
        Decode packet from bytes in frame.
        """
        self.frame = frame
        try:
            self.cmd = frame[0]
            if not self.cmd in [self.api_16_bit_adc, self.api_64_bit_adc]:
                logger.error( 'Unknown command %0x' % self.cmd)
                return

            self.length = length
            self.packet_size = length + 4
            self.address = '%0x%0x' % (frame[1], frame[2])
            self.rssi = frame[3]
            self.options = frame[4]
            self.num_samples = frame[5]

            channel_ind_1 = frame[6]
            channel_ind_2 = frame[7]

            # print '%0x, %0x' % (channel_ind_1, channel_ind_2)

            self.decode_channels(channel_ind_1, channel_ind_2)

            self.d_channels_data = [0 for x in range(0,9)]
            self.a_channels_data = [0 for x in range(0,8)]

            frame_byte = 8
            for n in range(0, self.num_samples):
                if self.have_d_channels:
                    self.d_data(frame[frame_byte], frame[frame_byte+1])
                    frame_byte += 2

                for adc_idx in range(0, len(self.a_channels_enabled)):
                    if self.a_channels_enabled[adc_idx]:
                        self.a_channels_data[adc_idx] += self.a_data(
                            frame[frame_byte], frame[frame_byte+1])
                        frame_byte += 2

        except IndexError:
            logger.error('Invalid XBee API frame: "{0}"'.format(frame))


    def get_adc(self, idx):
        return self.a_channels_data[idx]

    def __str__(self):
        res = []
        # res.append('frame: %s' % ' '.join(['%0x' % x for x in self.frame]))
        res.append('API data packet: ')
        if self.cmd is not None:
            res.append('cmd=%0x' % self.cmd)
        else:
            res.append('cmd=None')
        res.append('length=%d' % self.length)
        res.append('address=%s' % self.address)
        res.append('rssi=%d' % self.rssi)
        res.append('num.samples=%d' % self.num_samples)
        res.append('d channels: D0 [ %s ] D8' %
                   ' '.join([str(int(x)) for x in self.d_channels_enabled]))
        res.append('a channels: A0 [ %s ] A7' %
                   ' '.join([str(int(x)) for x in self.a_channels_enabled]))
        d_data = []
        for idx in range(0, len(self.d_channels_enabled)):
            if self.d_channels_enabled[idx]:
                d_data.append('D%d=%d'% (idx, self.d_channels_data[idx]))
                
        res.append('d data: %s' % ' '.join(d_data))

        a_data = []
        for idx in range(0, len(self.a_channels_enabled)):
            if self.a_channels_enabled[idx]:
                a_data.append('A%d=%d'% (idx, self.a_channels_data[idx]))

        res.append('a data: %s' % ' '.join(a_data))
        return '\n'.join(res)
                              

def read_packet(serl):
    """
    Generator function: reads one XBee API packet from given serial
    line and returns it
    """
    start_delim = 0x7E

    while True:

        while True:
            c = serl.read()
            if c == '':
                logger.info('read timeout')
                continue
            else:
                c = ord(c)
                # logger.info('read byte: "%0x"' % c)

            if c == start_delim:
                break

        length_high = serl.read()
        length_low = serl.read()
        length = ord(length_high) * 256 + ord(length_low)

        # logger.info('packet length: "%d"' % length)

        # lengh includes bytes starting from "83" through the last data byte.
        # it does not include 7E 00 1C and checksum (62)

        frame = []
        for idx in range(0, length):
            frame.append(ord(serl.read()))

        crc = ord(serl.read())

        # logger.info('frame: %s, crc=%0x' % (['%0x' % x for x in frame], crc))
        
        pkt = SerialIOPacket()
        pkt.decode_packet(frame, length)

        yield pkt


