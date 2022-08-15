from turtle import write
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from pynodered import node_red
import spidev
import time
from pprint import pprint


GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

keyHangers = int
GPIOs = [2,3,4,14,15,17,18,27,22,23,24,25,7,0,1,12,16,26,20,21]




class NFC():
    def __init__(self, bus=0, device=0,spd=100000):
        self.reader=SimpleMFRC522()
        self.close()

        

        self.boards = {}
        self.bus = bus
        self.device = device
        self.spd = spd

        for i in range(keyHangers):
            GPIO.setup(GPIOs[-(i+1)], GPIO.OUT)
            self.addBoard('reader'+str(i+1), GPIOs[-(i+1)])

    def reinit(self):
        self.reader.READER.spi = spidev.SpiDev()
        try:
            self.reader.READER.spi.open(self.bus, self.device)
            self.reader.READER.spi.max_speed_hz = self.spd
            self.reader.READER.MFRC522_Init()
        except:
            self.close()

    def close(self):
        self.reader.READER.spi.close()

    def addBoard(self, rid, pin):
        self.boards[rid] = pin

    def selectBoard(self, rid):
        if not rid in self.boards:
            print("readerid " + rid + " not found")
            return False

        for loop_id in self.boards:
            GPIO.output(self.boards[loop_id], loop_id == rid)
        return True

    def read(self, rid):
        if not self.selectBoard(rid):
            return None

        self.reinit()
        cid, val = self.reader.read_no_block()
        self.close()

        return val

    def write(self, rid, value):
        if not self.selectBoard(rid):
            return False

        self.reinit()
        self.reader.write_no_block(value)
        self.close()
        return True





while True:
    try:
        keyHangers = int(input("Enter how many key hangers are needed: "))
    except ValueError:
        print("sorry, I didn't understand that.")
        continue
    if keyHangers < 0:
        print("Your response must be positive")
    if keyHangers > 15:
        print("This can only support up to 15 hangers")
    else:
        break

nfc = NFC()



ledPins = []
for i in range(1,6):
    if i * (i-1) >= keyHangers:
        for j in range(i):
            ledPins.append(GPIOs[j])
        break

leds = []
for i in range(len(ledPins)):
    for j in range(len(ledPins)):
        if i != j:
            leds.append([ledPins[i],ledPins[j]])
leds = leds[:keyHangers]


print('Pins to connect RFID Reader RST pins to: ')
pprint(nfc.boards, sort_dicts=False)
print('')
print("**********")
print('')
print('Each pair of numbers surrounded by brackets represent the Raspberry Pi pins to connect the LEDs to. The first numbers is the Cathode connection and the second is the Anode. Each pair of numbers corresponds with an RFID reader that you found out how to configure above. The first pair corresponds with reader1, the second with reader2 and so on.')
pprint(leds)
 
@node_red(category="BookShelfFuncs")
def writeData(node, msg):
    BuildingInput = msg['payload']['BuildingInput']
    UnitInput = msg['payload']['UnitInput']
    writeText = BuildingInput+' '+UnitInput
    print(writeText)
    nfc.write('reader1', writeText)
    try:
        if nfc.read('reader1') != None:
            if nfc.read('reader1')[0:len(writeText)] == writeText:
                return {'payload':'Success'}
            else:
                return {'payload':'Try Again'}
        else:
            return {'payload':'Tag too far away!'}
    except:
        return {'payload':'Success'}


@node_red(category="BookShelfFuncs")
def readData(node,msg):
    books = []
    for reader in list(nfc.boards.keys())[1:]:
        if nfc.read(reader) != None:
            
            try:
                split = nfc.read(reader).split()
                books.append({"Building":split[0],"Unit":split[1]})
            except:
                books.append({"Building":"Empty","Unit":"Empty"})
        else:
            books.append({"Building":"Empty","Unit":"Empty"})
    books = {'payload':books}
    return books

@node_red(category="BookShelfFuncs")
def openBook(node,msg):
    led = leds[msg['payload']['id']]
    for i in range(3):
        GPIO.setup(led[0], GPIO.OUT)
        GPIO.setup(led[1], GPIO.OUT)
        GPIO.output(led[0], 0)
        GPIO.output(led[1],1)
        time.sleep(0.25)
        GPIO.setup(led[0], GPIO.IN)
        GPIO.setup(led[1], GPIO.IN)
        time.sleep(0.25)

"""writeData('e',{'payload':{'BuildingInput':'e','UnitInput':'f'}})
readData('e', 'e')
nfc.write('reader1','e')
print(nfc.read('reader1'))"""