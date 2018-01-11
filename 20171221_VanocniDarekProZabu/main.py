#!/usr/bin/python3
# Vanocni darek pro žábu 20171221; update 20180110 #
from secrets import APSSID, APSSIDPW, STSSIDPW, STSSID, SYNCMAC, NPPin, NPn
from machine import Timer, Pin, reset
from neopixel import NeoPixel
class Single(object):
  def __new__(cls, *args, **kwargs):
    if not hasattr(cls, "SINGLETON"):
      cls.SINGLETON = object.__new__(cls, *args, **kwargs)
    return cls.SINGLETON
  def __str__(self):
    return dir(self)
def Sync():
  from ntptime import settime; settime()
  from zvyk.sync import Sync as espZvykSync
  if espZvykSync(SYNCMAC):
    reset()
Single().np = NeoPixel(Pin(NPPin, Pin.OUT), NPn)
def present(rtc=None):
  s = Single()
  if hasattr(s, "keepRunning") and s.keepRunning:
    for i in range(s.np.n):
      s.np[i] = (
        round(s.power*(s.step/360)),
        round(s.power*(s.step%60/60)),
        round(s.power*((360-s.step)%120/120))
      )
    s.np[s.step%s.np.n if s.step%90 < 45 else (s.np.n-s.step)%s.np.n] = (
      s.power if s.step%120 > 60 else 0,
      s.power if s.step%60 > 30 else 0,
      s.power if s.step%90 < 45 else 0
    )
    s.np.write()
    if s.step%90==0:
      s.power *= 1.5
      s.power = round(2 if s.power > 255 else s.power)
    s.step = (s.step+1)%360
  else:
    if hasattr(s, "timer"):
      s.timer.deinit()
      del s.timer
    s.np.fill((0,0,0))
    s.np.write()
def init_present(rtc=None):
  s = Single()
  s.keepRunning = 1
  s.step = 0
  s.power = 32
  s.timer = Timer(-1)
  s.timer.init(period=100, mode=1, callback=present)
def stop():
  Single().keepRunning = 0
def wifi2connect(ssid=None, password=None):
  from network import WLAN, STA_IF
  STA = WLAN(STA_IF)
  STA.active(True)
  STA.disconnect()
  wfScan=STA.scan()
  nets=[]
  [nets.append(nw[0].decode("utf-8")) for nw in wfScan]
  if ssid in nets:
    STA.connect(ssid if ssid else APSSID, password if password else APSSIDPW)
  else:
    print("\n".join(nets), end="\n"+"="*80+"\n")
    STA.active(False)
def wifiAPpassword(pw=None):
  from network import WLAN, AP_IF, AUTH_WPA_WPA2_PSK
  AP = WLAN(AP_IF)
  AP.config(essid=STSSID, authmode=AUTH_WPA_WPA2_PSK, password=pw if pw else STSSIDPW)
init_present()
wifi2connect()