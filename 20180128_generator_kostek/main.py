#from zvyk.sync import Sync; Sync("2c:3a:e8:20:fa:c9"); from machine import reset; reset()
import time
#import mpu6050
#import mpuserver
import micropython
#from constants import *
micropython.alloc_emergency_exception_buf(100)



def isr(pin):
    print("Interrupt!")

print ('mpu = mpu6050.MPU()')

from machine import I2C, Pin
bus = I2C(scl=Pin(2), sda=Pin(0))
rate = 0x20

buffer = bytearray(16)
bytebuf = memoryview(buffer[0:1])
address = 0x68
accel_range = [2, 4, 8, 16]
gyro_range = [250, 500, 1000, 2000]


def write_byte(reg, val):
  bus.start()
  bytebuf[0] = val
  bus.writeto_mem(address, reg, bytebuf)
  bus.stop()


def read_byte(reg):
  bus.start()
  bus.readfrom_mem_into(address, reg, bytebuf)
  bus.stop()
  return bytebuf[0]

print (read_byte(0x75), 104)

# disable sleep mode and select clock source
#write_byte(0x6B, 0x01)
write_byte(0x6B, 0x00)

# explicitly set accel/gyro range
write_byte(0x1B, 0x00)
write_byte(0x1C, 0x00)


# enable all sensors
#write_byte(0x6C, 0)

# set sampling rate
write_byte(0x19, rate)

# enable dlpf
#write_byte(0x1A, 1)

sensors = bytearray(14)
calibration = [0] * 7
from ustruct import unpack

def read_sensors(f=0x3B):
  bus.readfrom_mem_into(address, f, sensors)
  data = unpack('>hhhhhhh', sensors)
  #print (sensors)
  # apply calibration values
  return [data[i] + calibration[i] for i in range(7)]

#  print (time.time(), read_sensors(0x3B, 16384.0), read_sensors(0x43, 131.0))
def run():
  while True:
    data = read_sensors(0x3B)
    print (
      time.time(),
      [data[i]/16384.0 for i in [0,1,2]],
      data[3]/360+36.53,
      [data[i]/131.0 for i in [4,5,6]]
      , read_sensors(0x43)
    )
    time.sleep_ms(100)
