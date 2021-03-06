import RPi.GPIO as IO
import time as T
import random as rnd
from queue import Queue
from threading import Thread


DEFAULT_BD = 1000
MODE_READ = 1
MODE_WRITE = 2


def byte2bits(a):
  bits = [
    1 == (a & 1),
    2 == (a & 2),
    4 == (a & 4),
    8 == (a & 8),
    16 == (a & 16),
    32 == (a & 32),
    64 == (a & 64),
    128 == (a & 128)
  ]
  return bits

def char2bits(char):
  return byte2bits(ord(char))


def bits2byte(bits):
  val = 0
  val = val | bits[0]
  val = val | (bits[1] << 1)
  val = val | (bits[2] << 2)
  val = val | (bits[3] << 3)
  val = val | (bits[4] << 4)
  val = val | (bits[5] << 5)
  val = val | (bits[6] << 6)
  val = val | (bits[7] << 7)
  return val

def bits2char(bits):
  return chr(bits2byte(bits))


class Data:
  def __init__(self, id, bits):
    self.id = id
    self.bits = bits

  def __str__(self):
    return "{id: %s, bits: %s}" % (str(self.id), str(self.bits))


class Client:
  def __init__(self, gpio_, bd_):
    self.gpio = gpio_
    self.bd = bd_
    self.delay = 1 / self.bd
    self.queueIn = Queue()
    self.queueOut = Queue()
    self._byteEvents = []
    self._broadcastEvents = []
    self._partnerEvents = []
    self._lineEvents = []
    self.lines = {}
    self.id = [False, False, False, False]
    self.idN = 0
    self.partners = {}
    self.selfSendId = False

  def setId(self, idN):
    self.idN = idN
    self.id = byte2bits(idN)[:4]

  def _setMode(self, mode):
    if mode == MODE_READ:
      IO.setup(self.gpio, IO.IN, pull_up_down=IO.PUD_DOWN)
    elif mode == MODE_WRITE:
      IO.setup(self.gpio, IO.OUT, initial=IO.HIGH)

  def _set(self, value):
    if value:
      IO.output(self.gpio, IO.HIGH)
    else:
      IO.output(self.gpio, IO.LOW)

  def _get(self):
    return IO.input(self.gpio)

  def _ioSync(self):
    while self._get():
      pass

  def _ioRead(self):
    T.sleep(self.delay * 1.5)
    bits = []
    for n in range(4 + 8):
      bits.append(self._get())
      T.sleep(self.delay)
    self.queueIn.put(bits)

  def _ioWait(self):
    if self.queueOut.empty():
      waitEnd = T.time() + (self.delay * 4)
      while not self._get():
        if T.time() > waitEnd:
          return True
      return False
    else:
      T.sleep(self.delay * (1 + rnd.random()))
      if not self._get():
        return True
      else:
        return False

  def _ioWrite(self):
    self._setMode(MODE_WRITE)
    self._set(1)
    T.sleep(self.delay * 2)
    data = self.queueOut.get()
    self.queueOut.task_done()
    self._set(0)
    T.sleep(self.delay)
    for bit in data.id:
      self._set(bit)
      T.sleep(self.delay)
    for bit in data.bits:
      self._set(bit)
      T.sleep(self.delay)
    self._set(0)

  def broadcast(self):
    self._sendData([False] * 4, [False] * 8)
    #print("broadcast")

  def sendId(self):
    if self.idN == 0:
      #print("no id to send! Redefining")
      self._defineId()
    else:
      self._sendData([False] * 4, self.id + ([False] * 4))
      #print("send id")

  def _defineId(self):
    oldIdN = self.idN
    for idN in range(1, 15 + 1):
      if not idN in self.partners:
        self.setId(idN)
        #print("Changed ID from %i to %i" % (oldIdN, idN))
        if oldIdN != self.idN:
          self.broadcast()
        elif (not self.selfSendId) and self.idN != 0:
          self.selfSendId = True
          self.sendId()
        return

  def _ioManager(self):
    while True:
      if self._ioWait():
        if not self.queueOut.empty():
          self._ioWrite()
      else:
        self._ioSync()
        self._ioRead()

  def _eventManager(self):
    while True:
      bits = self.queueIn.get()
      self.queueIn.task_done()
      addressBits = bits[:4] + ([0] * 4)
      dataBits = bits[4:]
      address = bits2byte(addressBits)
      data = bits2byte(dataBits)
      if address == 0 and data == 0:
        self.sendId()
        for broadcastEvent in self._broadcastEvents:
          broadcastEvent()
      elif address == 0:
        partnerid = dataBits[:4]
        partneridN = bits2byte(partnerid + ([False] * 4))
        self.partners[partneridN] = partnerid
        self._defineId()
        for partnerEvent in self._partnerEvents:
          partnerEvent(partneridN, partnerid)
      else:
        byte = bits2byte(dataBits)
        for byteEvent in self._byteEvents:
          byteEvent(bits2byte(addressBits), byte)
        if len(self._lineEvents) > 0:
          if not address in self.lines:
            self.lines[address] = ""
          if chr(byte) == "\n":
            for lineEvent in self._lineEvents:
              lineEvent(address, self.lines[address])
            self.lines[address] = ""
          else:
            self.lines[address] += chr(byte)

  def start(self):
    IO.setmode(IO.BCM)
    self._setMode(MODE_READ)
    Thread(target=self._ioManager, daemon=True).start()
    Thread(target=self._eventManager, daemon=True).start()
    self.broadcast()

  def _sendData(self, id, bits):
    self.queueOut.put(Data(id,bits))

  def sendStr(self, str):
    for char in str:
      self._sendData(self.id, char2bits(char))

  def sendBytes(self, bytes):
    for byte in bytes:
      self._sendData(self.id, byte2bits(byte))

  def onByte(self, callback):
    self._byteEvents.append(callback)
  def offByte(self, callback):
    self._byteEvents.remove(callback)

  def onBroadcast(self, callback):
    self._broadcastEvents.append(callback)
  def offBroadcast(self, callback):
    self._broadcastEvents.remove(callback)

  def onPartner(self, callback):
    self._partnerEvents.append(callback)
  def offPartner(self, callback):
    self._partnerEvents.remove(callback)

  def onLine(self, callback):
    self._lineEvents.append(callback)
  def offLine(self, callback):
    self._lineEvents.remove(callback)


def main(argv):
  gpio = 1
  if len(argv) > 0:
    gpio = int(argv[0])
  bd = 1000
  if len(argv) > 1:
    bd = int(argv[1])
  c = Client(gpio, bd)
  c.onLine(lambda address,line: print("%X: %s" % (address, line)))
  c.start()
  msg = "."
  while msg[:4] != "exit":
    msg = input(">>")
    if msg[:5] == "send " and len(msg) > 5:
      c.sendStr(msg[5:] + "\n")
    elif msg[:2] == "id":
      print("ID: %i = " % c.idN, c.id)
    elif msg[:7] == "partner":
      print("Partner\n", c.partners)
    elif msg[:7] == "set id " and len(msg) > 7:
      id = int(msg[7:])
      c.setId(id)
    elif msg[:5] == "lines":
      print("Lines\n", c.lines)
    elif msg[:4] == "help":
      print("send <msg>")
      print("id")
      print("set id <newId>")
      print("partners")
      print("lines")
      print("help")
      print("exit")
  print("ENDE")
  IO.cleanup()


if __name__=="__main__":
  import sys
  if len(sys.argv) > 1:
    main(sys.argv[1:])
  else:
    main([])
