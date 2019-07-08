import threading
import socketserver
import cmd
import re
import io


class CmdInterpreterException(ValueError): pass

def parseIntArbitraryBase(s):
    i = 0
    if s.startswith('0x'):
        i = int(s, 16)
    elif s.startswith('0b'):
        i = int(s, 2)
    else:
        i = int(s, 10)
    return i

class CmdInterpreter(cmd.Cmd):
    def __init__(self, infile, outfile, notifier, registers):
        super().__init__(stdin=infile, stdout=outfile)
        self.use_rawinput = False
        self.notifier = notifier
        self.registers = registers
        self.prompt = "test8> "
        self.intro = "test8 admin interface"
        self.splitterRe = re.compile('\s+')

    def __print(self, text):
        self.stdout.write(text)

    def __println(self, text):
        self.stdout.write(text)
        self.stdout.write("\n\r")

    def do_notify(self, arg):
        self.notifier.notify()

    def help_notify(self):
        self.__println("Notifies threads using the list of datapoints about changes in this list.")
        self.__println("Call after modifications on the list.")

    def do_quit(self, arg):
        self.__println("Bye!")
        return True
    
    def do_add(self, arg):
        try:
            (registerType, label, unit, address, count, scanrate, readTopic, writeTopic, feedbackTopic) = self.splitterRe.split(arg)
            self.__println("RegisterType:  {0}".format(registerType))
            self.__println("Label:         {0}".format(label))
            self.__println("Unit:          {0}".format(unit))
            self.__println("Address:       {0}".format(address))
            self.__println("Count:         {0}".format(count))
            self.__println("ScanRate:      {0}".format(scanrate))
            self.__println("ReadTopic:     {0}".format(readTopic))
            self.__println("WriteTopic:    {0}".format(writeTopic))
            self.__println("FeedbackTopic: {0}".format(feedbackTopic))

            if readTopic == 'None':
                readTopic = None
            if writeTopic == 'None':
                writeTopic = None
            if feedbackTopic == 'None':
                feedbackTopic = None
            unit = parseIntArbitraryBase(unit)
            address = parseIntArbitraryBase(address)
            count = parseIntArbitraryBase(count)
            scanrate = float(scanrate)
            if scanrate == 0:
                if readTopic:
                    raise CmdInterpreterException('readTopic must not be set when scanRate is zero')
                if not writeTopic:
                    raise CmdInterpreterException('writeTopic must be set when scanRate is zero')
                if not feedbackTopic:
                    raise CmdInterpreterException('feedbackTopic must be set when scanRate is zero')
            else:
                if not readTopic:
                    raise CmdInterpreterException('readTopic must be set when scanRate is zero')
                if writeTopic:
                    raise CmdInterpreterException('writeTopic must not be set when scanRate is zero')
                if feedbackTopic:
                    raise CmdInterpreterException('feedbackTopic must not be set when scanRate is zero')
            allowedRegisterTypes = ['HoldingRegister']
            if registerType not in allowedRegisterTypes:
                raise CmdInterpreterException('Unknown register type {0}, allowed are {1!s}'.format(registerType, allowedRegisterTypes))


        except ValueError as e:
            self.__println("ERROR: {0!s}, {1!s}".format(e.__class__.__name__, e))

    def help_add(self):
        # HoldingRegisterDatapoint('Voltage', 1, 0x2000, 2, datetime.timedelta(seconds=10), 'Pub/Voltage', None, None),
        self.__println("Usage: add <RegisterType> <Label> <Unit> <Address> <Count> <ScanRate>")
        self.__println("           <ReadTopic> <WriteTopic> <FeedbackTopic>")
        self.__println("---------------------------------------------------------------------")
        self.__println("<RegisterType>               One of HoldingRegister, ...")
        self.__println("<Label>                      Descriptive label")
        self.__println("<Unit>                       Modbus address of the device")
        self.__println("<Address>                    Register address within the device")
        self.__println("<Count>                      Count of registers to be read or write in words")
        self.__println("<ScanRate>                   Scanrate in seconds (float), for write datapoints")
        self.__println("                             set to zero (0)")
        self.__println("<ReadTopic>                  Topic to publish read data")
        self.__println("<WriteTopic>                 Topic to be subscribe to receive data to be")
        self.__println("                             written")
        self.__println("<FeedbackTopic>              Topic to publish feedback after a write process")
        self.__println("")
        self.__println("For read items the <ScanRate> must be non-zero, a <ReadTopic> must be set and")
        self.__println("<WriteTopic> and <FeedbackTopic> must be <None>.")
        self.__println("For write items the <ScanRate> must be zero, <ReadTopic> must be <None> and ")
        self.__println("<WriteTopic> and <FeedbackTopic> must be set.")

    def do_list(self, arg):
        for i, r in enumerate(self.registers):
            self.__println("#{0}: {1!s}".format(i, r))
    
    def help_list(self):
        self.__println("Usage: list")
        self.__println("-----------")
        self.__println("List the configured datapoints")

    def do_del(self, arg):
        try:
            i = int(arg)
            r = self.registers[i]
            self.registers.remove(r)
            self.__println("{0!s} removed".format(r))
        except ValueError as e:
            self.__println("ERROR: {0!s}".format(e))

    def help_del(self):
        self.__println("Usage: del <idx>")
        self.__println("Removes an item from the list of datapoints by its index, see list command.")
        self.__println("Be aware: indexes have been changed, rerun list before removing the next item.")


class CmdHandle(socketserver.StreamRequestHandler):
    def handle(self):
        cmd = CmdInterpreter(io.TextIOWrapper(self.rfile), io.TextIOWrapper(self.wfile), self.server.userData.notifier, self.server.userData.registers)
        try:
            cmd.cmdloop()
            print("Cmd handle terminated")
        except ConnectionAbortedError as e:
            print("Cmd handle externally interrupted")

class MyThreadingTCPServer(socketserver.ThreadingTCPServer):
    def __init__(self, host, handler, userData):
        super().__init__(host, handler)
        self.userData = userData

class MyCmdUserData(object):
    def __init__(self, notifier, registers):
        self.notifier = notifier
        self.registers = registers

class CmdServer(threading.Thread):
    def __init__(self, address, port, notifier, registers):
        super().__init__()
        self.server = MyThreadingTCPServer((address, port), CmdHandle, MyCmdUserData(notifier, registers))

    def start(self):
        self.server.serve_forever()


