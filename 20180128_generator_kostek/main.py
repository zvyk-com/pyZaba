#from zvyk.sync import Sync; Sync("5c:cf:7f:b8:9b:35"); from machine import reset; reset()
#import micropython
#micropython.alloc_emergency_exception_buf(100)
from machine import Timer, Pin, reset

### nastaveni --> možná předělat do importu (soubor)
PIN_NP = 14 # Len = 16
PIN_BUTT_ROLL = 0
POWER_NP = 1
DEEP_SLEEP_AFTER_SEC = 300

### aktuální pinout:
print (""" Nastavení pinů:
GPIO0(D3)   - připnutí tlačítka (červený drát)
GND         - připnutí země tlačítka (oranžový drát)
RST         - připnátí tlačítka2 (druhý červený drát)
GPIO14(D5)  - data NeoPixel pásku (už máš)
GND, VCC    - napájení NeoPixel pásku (už máš)
""")

### ntp a Synchronizace
def getNtp():
  from ntptime import settime; settime()

SYNCMAC = "5c:cf:7f:b8:9b:35"
def Sync():
  getNtp()
  from zvyk.sync import Sync as espZvykSync
  if espZvykSync(SYNCMAC):
    from machine import reset
    reset()

### příprava neopixel pro zobrazení hodů na ledkách
from neopixel import NeoPixel
isRolling = 0 # stav (že právě se provádí hod - abychom mohli ostatní aktivitu ignorovat
np = NeoPixel(Pin(PIN_NP, Pin.OUT), 16) # ledky CubeA(0-5); CubeB(6-11); (12-15) není potřeba mít
np.fill((0,0,POWER_NP)) # bootup modrá
np.write()

### uspání: vypne barvičky na ledkách, napíše dobrou, uspí se (aktuálně probouzím resetem)
def fallToSleep(rtc=None):
  np.fill((0,0,0))
  np.write()
  print ("Going to sleep. Bye")
  from machine import deepsleep
  deepsleep()

### Timer, který se každým hodem resetuje -> odkládá se tím uspání
autoSleep = Timer(-1)
def resetAutoSleep():
  locals()["autoSleep"].deinit()
  sleepAfter = locals()["DEEP_SLEEP_AFTER_SEC"] * 1000
  locals()["autoSleep"].init(period=sleepAfter, mode=0, callback=fallToSleep)
resetAutoSleep() # inicializace

### Net, json, socket => především k bonzování přes wifi o hodu kostek.
### urandom --> knihovna pro generování "náhodného čísla" která na esp není tak moc náhodná
from zvyk import net as zvyknet
Net = zvyknet.Net()
import urandom, json, socket
# aktualizuji adresu pro synchronizaci podle adresy zařízení
SYNCMAC = Net.getMac(Net.STA)

### práskací funkce, která po každém hodu nabonzuje jaký hod byl uskutečněn pokud je kostka připojena k wifi
def report(host="esp.zvyk.com", port=80, **kwargs):
  try:
    if Net.STA.isconnected():
      jData={}; jData["id"] = Net.getMac(Net.STA); jData["report"] = kwargs
      jData = json.dumps(jData)
      req = b"POST /report HTTP/1.0\r\nHost: {}\r\nContent-Length: {}\r\nContent-Type: application/json\r\n\r\n{}".format(host, len(jData), jData)
      del jData
      s = socket.socket();
      s.settimeout(3.0)
      s.connect(socket.getaddrinfo(host, port)[0][4])
      s.send(req)
      r = s.read().replace(b"\r\n\r\n",b" | ").replace(b"\r\n",b"; ")
      r = bytes.decode(r)
      print ("\033[0;33m{}\033[0m".format(r))
      del r
  except:
    print ("Exception on report", host, port, (kwargs))

### Tato funkce zajistí, nastavení správného času podle NTP, když bude připojena do wifi
### zároveň tato funkce (když hráč nehází) odhazuje každých 700ms náhodné číslo
### řekněme, že průběžně chrastí s kostkami v kelímku (tím zajištuji větší nahodilost "randomu")
# přepínač, zda-li se má pokusit načíst čas z internetu
doNtpRefresh = 1
def shakeAndNtp(rtc=None):
  urandom.getrandbits(16)
  if locals()["doNtpRefresh"] and Net.STA.isconnected():
    getNtp()
    locals()["doNtpRefresh"] = 0

### inicializace kelímkového šejkování pro zajištění "hezčejšího randomu"
shake = Timer(-1)
shake.init(period=700, mode=0, callback=shakeAndNtp)

### funkce na vykreslení čísla, které padlo na kosce:
def drawCub(number, shift=0):
  for i in range(number):
    np[i+shift] = (0,POWER_NP,POWER_NP)
  np.write()

### funkce vykreslí součet kostek binární reprezentací
def drowSumCubBinary(cubeA, cubeB, shift=0):
  mask = "".join(reversed(bin(cubeA+cubeB)[2:])) #[::-1]
  for i in range(len(mask)):
    if int(mask[i]):
      np[i+shift] = (0,POWER_NP,0)
  np.write()

### proces hodu
def roll(rtc=None):
  # getrandbits vrátí decimální čislo až maximálního rozsahu, udělám mu modulo, a povíším o 1
  cubeA = urandom.getrandbits(16)%6 + 1
  cubeB = urandom.getrandbits(16)%6 + 1
  # shoda hodnosti kostek
  match = cubeA==cubeB
  print ("Rolled: {} & {} | {}".format(cubeA, cubeB, match))
  # pokud je shoda kostek, nejdříve přebarvím pásek na žluto
  if match:
    np.fill((POWER_NP,POWER_NP,0))
    np.write()
  # vykreslím postupně kostky
  drawCub(cubeA)
  drawCub(cubeB,6)
  drowSumCubBinary(cubeA, cubeB, 12)
  # zkusím napráskat hod:)
  report(cubeA=cubeA, cubeB=cubeB, match=match)
  # uvolnění "zámku", "závory", "semaforu" -> hod je nyní dokončen
  # mohlibychom uvolnění naplánovat se zpožděním, aby bezprostředně po hodu nešlo opět hodit.
  # ideální místo k uvědomění si rozdílu mezi naplánováním a sleep
  locals()["isRolling"] = 0

### přijmutí impulsu pro hod
### funkce je volána v závislosti na zmáčknutí tlačítka -> kterým je vyvoláno přerušení
### měla by ste být taková logika, která co nejrychleji eliminule lidský negaritvní faktor
### a minimalizovaluje dvojzmáčknutí nebo držení tlačítka
### snahou je udělat izolovaný JEDEN hod -- Lidský faktor:( & práce s HW
doRoll = Timer(-1)
def initRoll(rtc=None):
  # naplánuji hod kostkou na zachvilku
  # po tuto chvilku nechám člověka, aby se vyblbnul s tlačítkem; zde je také prostor na vylepšení
  doRoll.deinit()
  doRoll.init(period=700, mode=0, callback=roll)
  # pokud se právě nehází:
  if not locals()["isRolling"]:
    locals()["isRolling"] = 1
    # vymažu předešlý hod (prázdnými barvami || fialovou pokud kostka není připojena do wifi)
    # bude sloužit jako podklad na kterém se zobrazí vržené kostky
    np.fill((0,0,0) if locals()["Net"].STA.isconnected() else (POWER_NP,0,POWER_NP))
    np.write()
    # poodložím uspání
    resetAutoSleep()

### nastavení HW tlačítka, které inicializuje hod
pRoll = Pin(PIN_BUTT_ROLL, Pin.IN, pull=Pin.PULL_UP)
pRoll.irq(lambda irq:initRoll(irq), Pin.IRQ_RISING | Pin.IRQ_FALLING)
