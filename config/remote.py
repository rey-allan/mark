import image
import lcd
import network
import sensor
import socket
import time
import ujson

from fpioa_manager import fm
from maix_motor import Maix_motor


# IO map for ESP32 on Maixduino
fm.register(25, fm.fpioa.GPIOHS10)
fm.register(8, fm.fpioa.GPIOHS11)
fm.register(9, fm.fpioa.GPIOHS12)
fm.register(28, fm.fpioa.GPIOHS13)
fm.register(26, fm.fpioa.GPIOHS14)
fm.register(27, fm.fpioa.GPIOHS15)

# Network card interface
nic = None

# Server info
wifi_ssid = 0
wifi_password = 0
server_ip = 0
server_port = 3456

# Camera angles
pan_angle = 90
tilt_angle = 90
# The wheel that supports the back of the robot
caster_wheel = 90


def _init():
    global nic

    lcd.display(image.Image("logo.jpg"))
    msg = "Scan QR code to share server WiFi information with M.A.R.K."
    num_rows = len(msg) // 28

    for i in range(num_rows + 3):
        lcd.draw_string(5, i * 15, msg[i * 28:i * 28 + 28], lcd.RED, lcd.WHITE)

    time.sleep(2)

    sensor.reset()
    sensor.set_pixformat(sensor.RGB565)
    sensor.set_framesize(sensor.QVGA)
    sensor.set_vflip(2)
    lcd.rotation(1)

    nic = network.ESP32_SPI(
        cs=fm.fpioa.GPIOHS10,
        rst=fm.fpioa.GPIOHS11,
        rdy=fm.fpioa.GPIOHS12,
        mosi=fm.fpioa.GPIOHS13,
        miso=fm.fpioa.GPIOHS14,
        sclk=fm.fpioa.GPIOHS15
    )
    print("ESP32_SPI firmware version:", nic.version())


def _scan_qr_code():
    global wifi_ssid
    global wifi_password
    global server_ip
    global server_port

    # Scan for the QR code to obtain the wifi and host info
    print("Scanning for QR codes...")

    while not wifi_ssid:
        img = sensor.snapshot()
        img.replace(vflip=True, hmirror=False, transpose=True)
        res = img.find_qrcodes()

        if len(res) > 0:
            payload = ujson.loads(res[0].payload())
            wifi_ssid = payload["ssid"]
            wifi_password = payload["password"]
            server_ip = payload["host"]
            server_port = payload["port"]

            print("Wifi: (ssid=" + wifi_ssid + ", password=" + "".join(["*"] * len(wifi_password)) + ")")
            print("Server: (ip=" + server_ip + ", port=" + str(server_port) + ")")

        lcd.display(img)


def _connect_to_wifi():
    err = 0
    print("Attempting to connect to network", wifi_ssid)

    while True:
        try:
            nic.connect(wifi_ssid, wifi_password)
            break
        except Exception:
            err += 1
            if err > 3:
                raise Exception("Failed to connect to network " + wifi_ssid)
            continue

    print(
        "Successfully connected to network",
        wifi_ssid,
        "(ip=" + nic.ifconfig()[0] + ", isConnected=" + str(nic.isconnected()) + ")"
    )


def _handle_message(data):
    global pan_angle
    global tilt_angle
    global caster_wheel

    if data == b"\x00":
        # Keepalive message sent by the app
        return
    elif data == b"\x01":
        Maix_motor.motor_motion(2, 1, 0)
    elif data == b"\x02":
        Maix_motor.motor_motion(1, 3, 0)
    elif data == b"\x03":
        Maix_motor.motor_motion(1, 4, 0)
    elif data == b"\x04":
        Maix_motor.motor_motion(2, 2, 0)
    elif data == b"\x05":
        Maix_motor.motor_run(0, 0, 0)
        caster_wheel = 90
    elif data == b"\x08":
        pan_angle = pan_angle + 2
    elif data == b"\x09":
        pan_angle = pan_angle - 2
    elif data == b"\x07":
        tilt_angle = tilt_angle + 2
    elif data == b"\x06":
        tilt_angle = tilt_angle - 2
    elif data == b"\x0b":
        caster_wheel = 40
    else:
        # Unrecognized command, no-op
        return

    # Constraint movements of the camera
    pan_angle = min(pan_angle, 180)
    pan_angle = max(pan_angle, 0)
    tilt_angle = min(tilt_angle, 180)
    tilt_angle = max(tilt_angle, 0)

    Maix_motor.servo_angle(1, pan_angle)
    Maix_motor.servo_angle(2, tilt_angle)
    Maix_motor.servo_angle(3, caster_wheel)


def _send_buffer(sock, data, buf_size):
    # Sends data to the given socket in chunks of `buf_size`
    block = int(len(data) / buf_size)
    send_len = 0

    for i in range(block):
        send_len += sock.send(data[i * buf_size:(i + 1) * buf_size])

    # Always send the last block in cases where `data` can't be divided exactly by `buf_size`
    send_len += sock.send(data[block * buf_size:])

    return send_len


def _send_camera_feed(sock):
    # Capture image from the camera feed
    img = sensor.snapshot()
    img.replace(vflip=True, hmirror=False, transpose=True)
    lcd.display(img)

    # Attempt to transmit compressed image
    img = img.compress(quality=30)
    send_len = _send_buffer(sock, img.to_bytes(), 2048)

    if send_len == 0:
        lcd.draw_string(lcd.width() // 2 - 68, lcd.height() // 2 - 4, "Video feed transmission failed", lcd.WHITE, lcd.RED)
        raise Exception("Video feed transmission failed")


def _receive_message(sock):
    data = sock.recv(1)
    _handle_message(data)


def _connect_to_server():
    sock = socket.socket()

    try:
        print("Attempting to connect to server: (" + server_ip + ":" + str(server_port) + ")")
        sock.connect((server_ip, server_port))
    except Exception as e:
        print("Caught exception when connecting to the server:", e)
        sock.close()
        return None

    print("Successfully connected to server")
    sock.settimeout(0.1)

    return sock


def _run():
    # Main loop
    while True:
        sock = _connect_to_server()
        if not sock:
            # Retry
            continue

        err = 0
        # Loop that listens to commands from the remote control app, and sends the video feed
        while True:
            try:
                _send_camera_feed(sock)
                _receive_message(sock)
            except OSError as e:
                if e.args[0] == 128:
                    print("Connection to remote server closed, will attempt to reconnect")
                    break
            except Exception as e:
                print("Encountered unexpected exception:", e)
                time.sleep(0.1)
                err += 1
                continue

            if err >= 10:
                print("Too many errors encountered. Connection to server will be re-established")
                break

        # Close socket before re-connecting
        sock.close()


_init()
_scan_qr_code()
_connect_to_wifi()
_run()
