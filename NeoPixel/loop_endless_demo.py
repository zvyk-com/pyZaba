from machine import Pin
from neopixel import NeoPixel
np=NeoPixel(Pin(5,Pin.OUT), 72) # podle poètu leds(72), pøipojených na GPIO5

np.fill((0,0,0))
np.write()

from math import pi, sin
power = 64

def demo():
  c = 0
  n = np.n
  while True: # Endless while ... ^C
    c = c%n
    for i in range(n):
      r = round(sin((n/4+i)%n*pi/n)*power*((c+n/4)%n/n))
      g = round(sin(i*pi/n)*power*(c/n))
      b = round(sin((n/2+i)%n*pi/n)*power*((c+n/2)%n/n))
      np[(c+i)%n] = (r, g, b)
    np.write()
    c += 1

demo()