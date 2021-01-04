import image
import lcd
import network
import os
import sensor
import socket
import time
import ujson
import utime

from fpioa_manager import board_info, fm
from machine import UART
from Maix import GPIO
from maix_motor import Maix_motor


lcd.display(image.Image('logo.jpg'))

msg = 'Open Code&Robots APP, enter your WiFi credentials and scan the resulting QR code with MARK camera'
num_rows = len(msg) // 28

for i in range(num_rows + 3):
    lcd.draw_string(5, i * 15, msg[i * 28:i * 28 + 28], lcd.RED, lcd.WHITE)

time.sleep(2)

# IO map for ESP32 on Maixduino
fm.register(25, fm.fpioa.GPIOHS10)
fm.register(8, fm.fpioa.GPIOHS11)
fm.register(9, fm.fpioa.GPIOHS12)
fm.register(28, fm.fpioa.GPIOHS13)
fm.register(26, fm.fpioa.GPIOHS14)
fm.register(27, fm.fpioa.GPIOHS15)

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.set_vflip(2)
lcd.rotation(1)

nic = network.ESP32_SPI(cs=fm.fpioa.GPIOHS10, rst=fm.fpioa.GPIOHS11, rdy=fm.fpioa.GPIOHS12, mosi=fm.fpioa.GPIOHS13, miso=fm.fpioa.GPIOHS14, sclk=fm.fpioa.GPIOHS15)
print('ESP32_SPI firmware version:', nic.version())

wifi_ssid = 0
wifi_password = 0
server_ip = 0
server_port = 3456

# Scan for the QR code to obtain the wifi and host info
print('Scanning for QR codes...')
while not wifi_ssid:
    img = sensor.snapshot()
    img.replace(vflip=True, hmirror=False, transpose=True)
    res = img.find_qrcodes()

    if len(res) > 0:
        payload = ujson.loads(res[0].payload())
        wifi_ssid = payload['ssid']
        wifi_password = payload['password']
        server_ip = payload['host']
        server_port = payload['port']
        print('Wifi: (ssid=' + wifi_ssid + ', password=' + ''.join(['*'] * len(wifi_password)) + ')')
        print('Host: (ip=' + server_ip + ', port=' + str(server_port) + ')')

    lcd.display(img)

err = 0

# First, connect to the given wifi
print('Attempting to connect to network', wifi_ssid)
while 1:
    try:
        nic.connect(wifi_ssid, wifi_password)
    except Exception as e:
        err += 1
        if err > 3:
            raise Exception('Failed to connect to network ' + wifi_ssid)
        continue
    break

print('Successfully connected to network', wifi_ssid, '(ip=' + nic.ifconfig()[0] + ', isConnected=' + str(nic.isconnected()) + ')')

pan_angle = 90
tilt_angle = 90
bullet = 90

def control_motors(data):
    # Executes the command to control the wheels or camera
    global pan_angle
    global tilt_angle
    global bullet

    if data == b'\x01':
        Maix_motor.motor_motion(2, 1, 0)
    if data == b'\x02':
        Maix_motor.motor_motion(1, 3, 0)
    if data == b'\x03':
        Maix_motor.motor_motion(1, 4, 0)
    if data == b'\x04':
        Maix_motor.motor_motion(2, 2, 0)
    if data == b'\x05':
        Maix_motor.motor_run(0, 0, 0)
        bullet = 90
    if data == b'\x08':
        pan_angle = pan_angle + 2
    if data == b'\x09':
        pan_angle = pan_angle - 2
    if data == b'\x07':
        tilt_angle = tilt_angle + 2
    if data == b'\x06':
        tilt_angle = tilt_angle - 2
    if data == b'\x0b':
        bullet = 40

    # Constraint movements of the camera
    if pan_angle > 180: pan_angle = 180
    if pan_angle < 1: pan_angle = 0
    if tilt_angle > 180: tilt_angle = 180
    if tilt_angle < 1: tilt_angle = 0

    Maix_motor.servo_angle(1, pan_angle)
    Maix_motor.servo_angle(2, tilt_angle)
    Maix_motor.servo_angle(3, bullet)

def send_buffer(sock, data, buf_size):
    # Sends data to the given socket in chunks of `buf_size`
    block = int(len(data) / buf_size)
    send_len = 0

    for i in range(block):
        send_len += sock.send(data[i * buf_size:(i + 1) * buf_size])

    # Always send the last block in cases where `data` can't be divided exactly by `buf_size`
    send_len += sock.send(data[block * buf_size:])

    return send_len

# Main loop that continuously tries to keep a connection open to the socket
while True:
    sock = socket.socket()

    try:
        print('Attempting to connect to socket: (' + server_ip + ':' + str(server_port) + ')')
        sock.connect((server_ip, server_port))
    except Exception as e:
        print('Caught exception when connecting to the socket:', e)
        sock.close()
        # Retry!
        continue

    print('Successfully connected to socket')
    sock.settimeout(0.1)

    err = 0

    # Loop that listens to commands from the remote control app, and sends the video feed
    while True:
        if err >= 10:
            print('Too many errors encountered. Connection to socket will be re-established')
            break

        # Capture image from the camera feed
        img = sensor.snapshot()
        img.replace(vflip=True, hmirror=False, transpose=True)
        img.draw_cross(120, 160)
        lcd.display(img)

        try:
            # Attempt to transmit compressed image
            img = img.compress(quality=30)
            send_len = send_buffer(sock, img.to_bytes(), 2048)

            if send_len == 0:
                lcd.draw_string(lcd.width() // 2 - 68, lcd.height() // 2 - 4, 'Video feed transmission failed', lcd.WHITE, lcd.RED)
                raise Exception('Video feed transmission failed')

            # Attempt to receive commands
            data = sock.recv(1)
            control_motors(data)
        except OSError as e:
            if e.args[0] == 128:
                lcd.draw_string(lcd.width() // 2 - 68, lcd.height() // 2 - 4, 'Connection to remote app closed', lcd.WHITE, lcd.RED)
                break
        except Exception as e:
            print('Encountered unexpected exception:', e)
            lcd.draw_string(lcd.width() // 2 - 68, lcd.height() // 2 - 4, 'Encountered exception; retrying...', lcd.WHITE, lcd.RED)
            time.sleep(0.1)
            err += 1
            continue

    # Close socket before re-connecting
    sock.close()
