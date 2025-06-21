import machine
from AP33772S import AP33772S
import time

#import smbus
#i2c = smbus.SMBus(1) # raspberry pi

i2c = machine.I2C(scl=machine.Pin(7), sda=machine.Pin(6), freq=400000) # esp32c3 xiao micropython

USB_PD = AP33772S(i2c=i2c)
print("Voltage is {:0.2f}V".format(USB_PD.get_voltage()))
print("Current is {:0.3f}A".format(USB_PD.get_current()))
print("Temperature is {:d}C".format(USB_PD.get_temp()))
USB_PD.set_output('OFF')
for pdo_num in range(1,14):
    pdo_list = USB_PD.get_pdo(pdo_num)
    if (pdo_list[1] != 'invalid' and pdo_list[2] > 1):
        print(pdo_list)

USB_PD.set_rdo(2,9.0,3.0)
USB_PD.set_output('AUTO')
time.sleep(2)
# USB_PD.set_rdo_reset() # this can cause loss of i2c communication, beware
time.sleep(2)
USB_PD.set_output('OFF')
