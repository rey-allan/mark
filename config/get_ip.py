"""Utility for obtaining the IP address of M.A.R.K."""
import network
import ujson

from fpioa_manager import fm


# IO map for ESP32 on Maixduino
fm.register(25, fm.fpioa.GPIOHS25)
fm.register(8, fm.fpioa.GPIOHS8)
fm.register(9, fm.fpioa.GPIOHS9)
fm.register(28, fm.fpioa.SPI1_D0, force=True)
fm.register(26, fm.fpioa.SPI1_D1, force=True)
fm.register(27, fm.fpioa.SPI1_SCLK, force=True)


def run():
    print('Reading network information')
    with open('network.json') as f:
        net = ujson.load(f)

    print('Connecting to network:', net['ssid'])
    nic = network.ESP32_SPI(cs=fm.fpioa.GPIOHS25, rst=fm.fpioa.GPIOHS8, rdy=fm.fpioa.GPIOHS9, spi=1)
    nic.connect(net['ssid'], net['password'])

    print('Successfully connected to network', net['ssid'], 'with IP=' + nic.ifconfig()[0])
