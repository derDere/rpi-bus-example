import RPi.GPIO as IO
import time as T

class Sender:
  def __init__(self, ioNr, Bd):
    self._io = ioNr
    self._bd = Bd
    self.delay = 1 / Bd
    IO.setup(self._io, IO.OUT, initial=IO.HIGH)

  def set(self, value):
    if value:
      IO.output(self._io, IO.HIGH)
    else:
      IO.output(self._io, IO.LOW)

  def send(self, byte):
    self.set(0)
    T.sleep(self.delay)
    for bit in byte:
      self.set(bit)
      T.sleep(self.delay)
    self.set(1)
    T.sleep(self.delay * 2)


def char2bits(char):
  a = ord(char)
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


def send(message):
  bytes = []
  for c in message:
    bytes.append(char2bits(c))
  IO.setmode(IO.BCM)
  s = Sender(21, 9600)
  input()
  s.set(1)
  T.sleep(s.delay * 2)
  for byte in bytes:
    s.send(byte)
  input()


def main(argv):
  try:
    IO.cleanup()
  except:
    pass
  if len(argv) > 0:
    if argv[0] == 'test':
      Bd = 100
      if len(argv) > 1:
        Bd = int(argv[1])
      test(Bd)
    elif argv[0] == 'send':
      msg = "Hello World!"
      if len(argv) > 1:
        msg = argv[1]
      send(msg)
  IO.cleanup()


def test(Bd):
  IO.setmode(IO.BCM)
  s = Sender(21, Bd)
  bit = True
  while True:
    s.set(bit)
    if bit:
      print('__._|__ = 1')
    else:
      print('__|_.__ = 0')
    bit = not bit
    T.sleep(1 / Bd)

if __name__=="__main__":
  import sys
  if len(sys.argv) > 1:
    main(sys.argv[1:])
  else:
    main([])
