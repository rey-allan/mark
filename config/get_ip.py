"""Utility for obtaining the IP address of M.A.R.K."""
import network
import ujson

from fpioa_manager import board_info, fm


# IO map for ESP32 on Maixduino
fm.register(25, fm.fpioa.GPIOHS10)
fm.register(8, fm.fpioa.GPIOHS11)
fm.register(9, fm.fpioa.GPIOHS12)
fm.register(28, fm.fpioa.GPIOHS13)
fm.register(26, fm.fpioa.GPIOHS14)
fm.register(27, fm.fpioa.GPIOHS15)

def run():
    print('Reading network information')
    with open('network.json') as f:
        net = ujson.load(f)

    print('Connecting to network:', net['ssid'])
    nic = network.ESP32_SPI(cs=fm.fpioa.GPIOHS10, rst=fm.fpioa.GPIOHS11, rdy=fm.fpioa.GPIOHS12,
                            mosi=fm.fpioa.GPIOHS13, miso=fm.fpioa.GPIOHS14, sclk=fm.fpioa.GPIOHS15)
    nic.connect(net['ssid'], net['password'])

    print('Successfully connected to network', net['ssid'], 'with IP=' + nic.ifconfig()[0])
