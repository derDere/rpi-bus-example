import RPi.GPIO as IO
import time as T


class Receiver:
  def __init__(self, ioNr, Bd):
    self._io = ioNr
    self._bd = Bd
    self.delay = 1 / self._bd
    IO.setup(self._io, IO.IN)

  def get(self):
    return IO.input(self._io)

  def read(self):
    bits = []
    while self.get():
      pass
    T.sleep(self.delay * 1.5)
    for n in range(8):
      bit = self.get();
      bits.append(bit)
      T.sleep(self.delay)
    T.sleep(self.delay * 0.6)
    return bits


def bits2Char(bits):
  val = 0
  val = val | bits[0]
  val = val | (bits[1] << 1)
  val = val | (bits[2] << 2)
  val = val | (bits[3] << 3)
  val = val | (bits[4] << 4)
  val = val | (bits[5] << 5)
  val = val | (bits[6] << 6)
  val = val | (bits[7] << 7)
  return chr(val)


def read():
  IO.setmode(IO.BCM)
  r = Receiver(26, 9600)
  while True:
    c = bits2Char(r.read())
    if c != '\0':
      print(c, end='', flush=True)


def main(argv):
  if len(argv) > 0:
    if argv[0] == 'test':
      Bd = 100
      if len(argv) > 1:
        Bd = int(argv[1])
      test(Bd)
    elif argv[0] == 'read':
      read()


def test(Bd):
  IO.setmode(IO.BCM)
  r = Receiver(26, Bd)
  m1 = False
  while True:
    v = r.get()
    if v != m1:
      if r.get():
        print('__._|__ = 1')
      else:
        print('__|_.__ = 0')
    else:
      print('#############################################')
    m1 = v
    T.sleep(1 / Bd)


if __name__=="__main__":
  import sys
  if len(sys.argv) > 1:
    main(sys.argv[1:])
  else:
    main([])
