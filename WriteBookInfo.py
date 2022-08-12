import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from pynodered import node_red
import spidev
import time
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

leds = {
    "1":24,
    "2":22,
    "3":27,
    "4":17
}

for i in range(len(list(leds.values()))):
    GPIO.setup(list(leds.values())[i], GPIO.OUT)

class NFC():
    def __init__(self, bus=0, device=0,spd=1000000):
        self.reader=SimpleMFRC522()
        self.close()
        
        GPIO.setup(5, GPIO.OUT)
        GPIO.setup(6, GPIO.OUT)
        GPIO.setup(13, GPIO.OUT)
        GPIO.setup(19, GPIO.OUT)

        self.boards = {}
        self.bus = bus
        self.device = device
        self.spd = spd

    def reinit(self):
        self.reader.READER.spi = spidev.SpiDev()
        self.reader.READER.spi.open(self.bus, self.device)
        self.reader.READER.spi.max_speed_hz = self.spd
        self.reader.READER.MFRC522_Init()

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

nfc = NFC()
nfc.addBoard("reader1",5)
nfc.addBoard("reader2",6)
nfc.addBoard("reader3",13)
nfc.addBoard("reader4",19)

    
@node_red(category="BookShelfFuncs")
def writeData(node, msg):
    TitleInput = msg['payload']['TitleInput']
    AuthorInput = msg['payload']['AuthorInput']
    writeText = TitleInput+' '+AuthorInput
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
        return {'payload':'Error! Despair!'}


@node_red(category="BookShelfFuncs")
def readData(node,msg):
    books = []
    for reader in range(1,len(list(nfc.boards.keys()))):
        try:
            split = nfc.read(list(nfc.boards.keys())[reader]).split()
            books.append({"Title":split[0],"Author":split[1]})
        except:
            books.append({"Title":"Empty","Author":"Empty"})
    books = {'payload':books}
    return books

@node_red(category="BookShelfFuncs")
def openBook(node,msg):
    for i in range(10):
        GPIO.output(leds[str(msg['payload']['id']+1)], 1)
        time.sleep(0.25)
        GPIO.output(leds[str(msg['payload']['id']+1)], 0)
        time.sleep(0.25)

