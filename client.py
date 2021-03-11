import RPi.GPIO as IO
import time as T
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
  return bit

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


class Client:
  def __init__(self, gpio_, bd_):
    self.gpio = gpio_
    self.bd = bd_
    self.delay = 1 / self.bd
    self.queueIn = Queue()
    self.queueOut = Queue()
    self._byteEvents = []

  def setMode(self, mode):
    if mode == MODE_READ:
      IO.setup(self.gpio, IO.IN)
    elif mode == MODE_WRITE:
      IO.setup(self.gpio, IO.OUT, initial=IO.HIGH)

  def set(self, value):
    if value:
      IO.output(self.gpio, IO.HIGH)
    else:
      IO.output(self.gpio, IO.LOW)

  def get(self):
    return IO.input(self.gpio)

  def sendByte(self, byte):
    self.set(0)
    T.sleep(self.delay)
    for bit in byte:
      self.set(bit)
      T.sleep(self.delay)
    self.set(1)
    T.sleep(self.delay * 2)

  def readByte(self):
    bits = []
    timeoutCounter = 0
    while self.get():
      T.sleep(self.delay * (1/1000))
      timeoutCounter += 1
      if timeoutCounter >= 1000:
        timeoutCounter = 0
        if not self.queueOut.empty():
          return []
    T.sleep(self.delay * 0.5)
    for n in range(8):
      T.sleep(self.delay)
      bit = self.get();
      bits.append(bit)
    T.sleep(self.delay * 0.6)
    return bits

  def _ioManager(self):
    while True:
      if not self.queueOut.empty():
        T.sleep(self.delay * rnd.random())
        if not self.get():
          self.setMode(MODE_WRITE)
          T.sleep(self.delay * 1.1)
          self.sendByte(self.queueOut.get())
          self.setMode(MODE_READ)
      bits = self.readByte()
      if len(bits) > 0:
        self.queueIn.put(bits)

  def _eventManager(self):
    while True:
      bits = self.queueIn.get()
      for byteEvent in self._byteEvents:
        byteEvent(bits2byte(bits))
      #####################
      #print(bits2char(bits), end='', flush=True)

  def start(self):
    IO.setmode(IO.BCM)
    self.setMode(MODE_READ)
    Thread(target=self._ioManager, daemon=True).start()
    Thread(target=self._eventManager, daemon=True).start()

  def sendStr(self, str):
    for char in str:
      self.queueOut.put(char2bits(char))

  def sendBytes(self, bytes):
    for byte in bytes:
      self.queueOut.put(byte2bits(byte))

  def onByte(self, callback):
    self._byteEvents.append(callback)

  def offByte(self, callback):
    self._byteEvents.remove(callback)


def main(argv):
  gpio = 1
  if len(argv) > 0:
    gpio = int(argv[0])
  bd = 1000
  if len(argv) > 1:
    bd = int(argv[1])
  c = Client(gpio, bd)
  c.onByte(lambda b: print(chr(b), end='', flush=True))
  c.start()
  msg = "xxx"
  while len(msg) > 0:
    msg = input()
    if len(msg) > 0:
      c.sendStr(msg)


if __name__=="__main__":
  import sys
  if len(sys.argv) > 1:
    main(sys.argv[1:])
  else:
    main([])
