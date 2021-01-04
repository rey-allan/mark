import gc
import image
import lcd
import Maix
import time
import os

from fpioa_manager import *
from gpio import speaker
from Maix import FPIOA, GPIO

gc.threshold(65536)


def exception_output(e):
    lcd.clear()

    if str(e) == '[Errno 5] EIO':
        e = 'EIO Error - please turn on the power switch and reboot MARK'
    print(e)

    num_rows = len(str(e)) // 30 + 1

    for i in range(num_rows):
        lcd.draw_string(0, i * 15, str(e)[i * 30:i * 30 + 30], lcd.RED, lcd.BLACK)

    time.sleep(5)


try:
    lcd.init()
    lcd.rotation(1)
    lcd.display(image.Image('logo.jpg'))

    boot_pressed = 0
    boot_pin = 16
    fpioa = FPIOA()
    fpioa.set_function(boot_pin, FPIOA.GPIO7)
    boot_gpio = GPIO(GPIO.GPIO7, GPIO.IN)

    # Wait for user to press the boot pin
    start_time =  time.ticks_ms()
    while (time.ticks_ms() - start_time) < 500:
        if boot_gpio.value() == 0:
            boot_pressed += 1
            time.sleep(0.5)
            start_time = time.ticks_ms()

    print('Boot pressed: ' + str(boot_pressed))

    # Load default MARK features
    if boot_pressed == 2:
        lcd.draw_string(0, 0, 'Loading default MARK features...', lcd.RED, lcd.BLACK)
        time.sleep(5)
        lcd.clear()
        gc.collect()
        from preloaded import *

    # Enter remote mode to control MARK using app
    if boot_pressed > 2:
        lcd.draw_string(0, 0, 'Entering remote mode...', lcd.RED, lcd.BLACK)
        time.sleep(5)
        from remote import *

    # By default, run user-defined code (i.e. our programs!)
    gc.collect()
    from user import *
except Exception as e:
    exception_output(e)
    raise
