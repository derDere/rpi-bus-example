from client import Client
import RPi.GPIO as IO
import atexit
import argparse
from datetime import datetime
import npyscreen as npys


def Now():
  t = datetime.now()
  return t.strftime("%H:%M")


class ActionControllerSearch(npys.ActionControllerSimple):
  def create(self):
    self.add_action('^/.*', self.enterCommand, False)
    self.add_action('^:.*', self.sendMessage, False)

  def sendMessage(self, command_line, widget_proxy, live):
    global nick, send
    msg = command_line[1:]
    self.parent.addMsg(nick, msg)
    send(msg)

  def enterCommand(self, command_line, widget_proxy, live):
    global commands
    cmd = command_line[1:]
    if cmd in commands:
      commands[cmd]()
    else:
      self.parent.addInfo("Unknown command")

class ChatForm(npys.FormMuttActiveTraditional):
  ACTION_CONTROLLER = ActionControllerSearch
  def addMsg(self, who, msg):
    global margin, grayscale
    who += ":"
    who = Now() + "| " + who
    who = who + (" " * (margin - len(who)))
    #line = "\033[92m%s\033[96m%s\033[0m%s" % (who[:6], who[6:], msg)
    line = "%s%s%s" % (who[:6], who[6:], msg)
    self.wMain.values.insert(0, line)
    self.wMain.display()

  def addInfo(self, Info):
    global margin
    self.wMain.values.insert(0, (" " * margin) + Info)
    self.wMain.display()

class ChatApp(npys.NPSApp):
  def main(self):
    global nick
    self.chatForm = ChatForm()
    self.chatForm.wStatus1.value = "GPIO Chat - Logged in as: %s" % nick
    self.chatForm.wStatus2.value = 'Chat = ":", Cmd = "/", Help = "/?"'
    self.chatForm.value.set_values([])
    self.chatForm.wMain.values = self.chatForm.value.get()
    self.chatForm.wMain.editable = False
    self.chatForm.edit()


def main(argv):

  global grayscale, margin, nick, terminal, client, nicks, send, capp, commands, run

  def sendNick():
    client.sendStr("/nick %s\n" % nick)

  def RequestNick(idn):
    client.sendStr("/whois %i\n" % idn)

  def Send(msg):
    client.sendStr("#%s\n" % msg)
  send = Send

  def OnPartner(idn, id):
    RequestNick(idn)

  def SwitchCase_WhoIs(address, idN):
    global client, nick
    if int(idN) == client.idN:
      sendNick()

  def SwitchCase_Nick(address, partnerNick):
    global nicks
    nicks[address] = partnerNick

  def PrintMessage(who, msg):
    who += ":"
    who = Now() + "| " + who
    who += (" " * (margin - len(who)))
    print("\r\033[92m%s\033[96m%s\033[0m%s" % (who[0:6], who[6:], msg))

  def OnChatLine(address, line):
    global capp, nicks, terminal, margin
    if line[0] == "/":
      linedata = line[1:].split(" ")
      switchCase = {
        "whois": SwitchCase_WhoIs,
        "nick": SwitchCase_Nick
      }
      if linedata[0] in switchCase:
        switchCase[linedata[0]](address, *linedata[1:])
    elif line[0] == "#":
      who = "%X" % address
      if address in nicks:
        who = nicks[address]
      if terminal:
        PrintMessage(who, line[1:])
      else:
        capp.chatForm.addMsg(who, line[1:])

  def PrintInfo(*InfoLines):
    global capp, terminal, margin
    for Info in InfoLines:
      if terminal:
        print(bcolors.OKBLUE + (" " * margin) + Info + bcolors.ENDC)
      else:
        capp.chatForm.addInfo(Info)

  argParser = argparse.ArgumentParser(description="Chat using a bus on one GPIO")
  argParser.add_argument("gpio", help="Defines which GPIO to use to chat on", type=int)
  argParser.add_argument("nick", help="Sets your nickname for the chat", type=str)
  argParser.add_argument("-b", "--baudrate", help="Defines how much bits per second are send or received. To high numbers will result in transmission errors! (Default: 100)", default=100, type=int)
  argParser.add_argument("-m", "--margin", help="Defines how width the nickname columen should be. (Default: 24)", default=24, type=int)
  #argParser.add_argument("-g", "--grayscale", help="Turns off colors.", action="store_true")
  argParser.add_argument("-t", "--terminal", help="Turns off fancy displaying.", action="store_true")
  args = argParser.parse_args()
  #
  nicks = {}
  #grayscale = args.grayscale
  margin = args.margin
  nick = args.nick
  terminal = args.terminal
  #
  client = Client(args.gpio, args.baudrate)
  client.onLine(OnChatLine)
  client.onPartner(OnPartner)
  client.start()
  #
  printHelp = lambda: PrintInfo("Line 1", "Line 2", "/exit    Exit application.")
  commands = {
    "exit": lambda: exit(),
    "?": printHelp,
    "help": printHelp
  }
  #
  if not terminal:
    capp = ChatApp()
    capp.send = Send
    capp.run()
  else:
    run = True
    PrintInfo("Enter /? for help")
    while run:
      cmd = input()
      if cmd[0] == "/":
        if cmd[1:] in commands:
          commands[cmd[1:]]()
        else:
          PrintInfo("Unknown command")
      else:
        Send(cmd)
        PrintMessage(nick, cmd)


@atexit.register
def OnExit():
  IO.cleanup()


if __name__=="__main__":
  import sys
  if len(sys.argv) > 1:
    main(sys.argv[1:])
  else:
    main([])
