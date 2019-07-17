import threading
import socketserver
import cmd
import re
import io
import datetime
import RegisterDatapoint
import logging

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
    def __init__(self, infile, outfile, config, notifier, registers):
        super().__init__(stdin=infile, stdout=outfile)
        self.use_rawinput = False
        self.config = config
        self.notifier = notifier
        self.registers = registers
        self.prompt = "test8> "
        self.intro = "test8 admin interface"
        self.splitterRe = re.compile('\s+')
        self.logger = logging.getLogger('CmdInterpreter')

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
    
    def do_add_hr(self, arg):
        try:
            (label, unit, address, count, scanrate, readTopic, writeTopic, feedbackTopic, converter) = self.splitterRe.split(arg)
            self.__println("Label:         {0}".format(label))
            self.__println("Unit:          {0}".format(unit))
            self.__println("Address:       {0}".format(address))
            self.__println("Count:         {0}".format(count))
            self.__println("ScanRate:      {0}".format(scanrate))
            self.__println("ReadTopic:     {0}".format(readTopic))
            self.__println("WriteTopic:    {0}".format(writeTopic))
            self.__println("FeedbackTopic: {0}".format(feedbackTopic))
            self.__println("Converter:     {0}".format(converter))

            if readTopic == 'None':
                readTopic = None
            if writeTopic == 'None':
                writeTopic = None
            if feedbackTopic == 'None':
                feedbackTopic = None
            if converter == 'None':
                converter = None
            unit = parseIntArbitraryBase(unit)
            address = parseIntArbitraryBase(address)
            count = parseIntArbitraryBase(count)
            scanrate = float(scanrate)
            r = RegisterDatapoint.HoldingRegisterDatapoint(label, unit, address, count, datetime.timedelta(seconds=scanrate), readTopic, writeTopic, feedbackTopic, converter)
            self.registers.append(r)
        except ValueError as e:
            self.__println("ERROR: {0!s}, {1!s}".format(e.__class__.__name__, e))

    def help_add_hr(self):
        # HoldingRegisterDatapoint('Voltage', 1, 0x2000, 2, datetime.timedelta(seconds=10), 'Pub/Voltage', None, None),
        self.__println("Usage: add_hr <Label> <Unit> <Address> <Count> <ScanRate>")
        self.__println("              <ReadTopic> <WriteTopic> <FeedbackTopic>")
        self.__println("              <Converter>")
        self.__println("Adds a holding register")
        self.__println("DO NOT FORGET TO SAVE AFTERWARDS!")
        self.__println("---------------------------------------------------------------------")
        self.__println("<Label>                      Descriptive label")
        self.__println("<Unit>                       Modbus address of the device")
        self.__println("<Address>                    Register address within the device")
        self.__println("<Count>                      Count of registers to be read or write in words")
        self.__println("<ScanRate>                   Scanrate in seconds (float), for write datapoints")
        self.__println("                             set to zero (0)")
        self.__println("<ReadTopic>                  Topic to publish read data")
        self.__println("<WriteTopic>                 Topic to be subscribe to receive data to be")
        self.__println("                             written")
        self.__println("<FeedbackTopic>              Topic to publish feedback after a write process,")
        self.__println("<Converter>                  Converter for data")

    
    def do_add_coil(self, arg):
        try:
            (label, unit, address, scanrate, readTopic, writeTopic, feedbackTopic) = self.splitterRe.split(arg)
            self.__println("Label:         {0}".format(label))
            self.__println("Unit:          {0}".format(unit))
            self.__println("Address:       {0}".format(address))
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
            scanrate = float(scanrate)
            r = RegisterDatapoint.CoilDatapoint(label, unit, address, datetime.timedelta(seconds=scanrate), readTopic, writeTopic, feedbackTopic)
            self.registers.append(r)
        except ValueError as e:
            self.__println("ERROR: {0!s}, {1!s}".format(e.__class__.__name__, e))

    def help_add_coil(self):
        self.__println("Usage: add_coil <Label> <Unit> <Address> <ScanRate>")
        self.__println("                <ReadTopic> <WriteTopic> <FeedbackTopic>")
        self.__println("Adds a coil")
        self.__println("DO NOT FORGET TO SAVE AFTERWARDS!")
        self.__println("---------------------------------------------------------------------")
        self.__println("<Label>                      Descriptive label")
        self.__println("<Unit>                       Modbus address of the device")
        self.__println("<Address>                    Register address within the device")
        self.__println("<ScanRate>                   Scanrate in seconds (float), for write datapoints")
        self.__println("                             set to zero (0)")
        self.__println("<ReadTopic>                  Topic to publish read data")
        self.__println("<WriteTopic>                 Topic to be subscribe to receive data to be")
        self.__println("                             written")
        self.__println("<FeedbackTopic>              Topic to publish feedback after a write process,")
    
    def do_add_ir(self, arg):
        try:
            (label, unit, address, count, scanrate, updateOnly, readTopic, converter) = self.splitterRe.split(arg)
            self.__println("Label:         {0}".format(label))
            self.__println("Unit:          {0}".format(unit))
            self.__println("Address:       {0}".format(address))
            self.__println("Count:         {0}".format(count))
            self.__println("ScanRate:      {0}".format(scanrate))
            self.__println("UpdateOnly:    {0}".format(updateOnly))
            self.__println("ReadTopic:     {0}".format(readTopic))
            self.__println("Converter:     {0}".format(converter))

            if readTopic == 'None':
                readTopic = None
            if converter == 'None':
                converter = None
            if updateOnly in ['true', 'True', 'yes', 'Yes']:
                updateOnly = True
            elif updateOnly in ['false', 'False', 'no', 'No']:
                updateOnly = False
            else:
                raise CmdInterpreterException('updateOnly must be true or false, yes or no')
            unit = parseIntArbitraryBase(unit)
            address = parseIntArbitraryBase(address)
            count = parseIntArbitraryBase(count)
            scanrate = float(scanrate)
            r = RegisterDatapoint.InputRegisterDatapoint(label, unit, address, count, datetime.timedelta(seconds=scanrate), updateOnly, readTopic, converter)
            self.registers.append(r)
        except ValueError as e:
            self.__println("ERROR: {0!s}, {1!s}".format(e.__class__.__name__, e))

    def help_add_ir(self):
        self.__println("Usage: add_ir <Label> <Unit> <Address> <Count> <ScanRate>")
        self.__println("              <UpdateOnly> <ReadTopic> <Converter>")
        self.__println("Adds an input register")
        self.__println("DO NOT FORGET TO SAVE AFTERWARDS!")
        self.__println("---------------------------------------------------------------------")
        self.__println("<Label>                      Descriptive label")
        self.__println("<Unit>                       Modbus address of the device")
        self.__println("<Address>                    Register address within the device")
        self.__println("<Count>                      Count of registers to be read in words")
        self.__println("<ScanRate>                   Scanrate in seconds (float)")
        self.__println("<UpdateOnly>                 Publish only when value has changed")
        self.__println("<ReadTopic>                  Topic to publish read data")
        self.__println("<Converter>                  Converter for data")

    def do_add_di(self, arg):
        try:
            (label, unit, address, count, scanrate, updateOnly, readTopic, bitCount) = self.splitterRe.split(arg)
            self.__println("Label:         {0}".format(label))
            self.__println("Unit:          {0}".format(unit))
            self.__println("Address:       {0}".format(address))
            self.__println("Count:         {0}".format(count))
            self.__println("ScanRate:      {0}".format(scanrate))
            self.__println("UpdateOnly:    {0}".format(updateOnly))
            self.__println("ReadTopic:     {0}".format(readTopic))
            self.__println("BitCount:      {0}".format(bitCount))

            if readTopic == 'None':
                readTopic = None
            if updateOnly in ['true', 'True', 'yes', 'Yes']:
                updateOnly = True
            elif updateOnly in ['false', 'False', 'no', 'No']:
                updateOnly = False
            else:
                raise CmdInterpreterException('updateOnly must be true or false, yes or no')
            unit = parseIntArbitraryBase(unit)
            address = parseIntArbitraryBase(address)
            count = parseIntArbitraryBase(count)
            scanrate = float(scanrate)
            bitCount = int(bitCount)
            r = RegisterDatapoint.DiscreteInputDatapoint(label, unit, address, count, datetime.timedelta(seconds=scanrate), updateOnly, readTopic, None, bitCount)
            self.registers.append(r)
        except ValueError as e:
            self.__println("ERROR: {0!s}, {1!s}".format(e.__class__.__name__, e))

    def help_add_di(self):
        self.__println("Usage: add_di <Label> <Unit> <Address> <Count> <ScanRate>")
        self.__println("              <UpdateOnly> <ReadTopic> <bitCount>")
        self.__println("Adds a discrete input")
        self.__println("DO NOT FORGET TO SAVE AFTERWARDS!")
        self.__println("---------------------------------------------------------------------")
        self.__println("<Label>                      Descriptive label")
        self.__println("<Unit>                       Modbus address of the device")
        self.__println("<Address>                    Register address within the device")
        self.__println("<Count>                      Count of registers to be read in words")
        self.__println("<ScanRate>                   Scanrate in seconds (float)")
        self.__println("<UpdateOnly>                 Publish only when value has changed")
        self.__println("<ReadTopic>                  Topic to publish read data")
        self.__println("<BitCount>                   Number of bit to be considered")

    def do_list(self, arg):
        for i, r in enumerate(self.registers):
            self.__println("#{0}: {1!s}".format(i, r))
    
    def help_list(self):
        self.__println("Usage: list")
        self.__println("-----------")
        self.__println("List the configured datapoints")

    def do_reset(self, arg):
        for r in self.registers:
            r.errorCount = 0
            r.processCount = 0
    
    def help_reset(self):
        self.__println("Usage: reset")
        self.__println("-----------")
        self.__println("Resets the statistics of configured datapoints")

    def do_stats(self, arg):
        for i, r in enumerate(self.registers):
            if r.processCount == 0:
                ratio = -1
            else:
                ratio = float(r.errorCount) / float(r.processCount)
            self.__println("#{0:2d}: {1:15s} ({2:2d}, {3:5d}), pc: {4:7d}, ec: {5:7d}, q: {6:1.4f}"
                           .format(i, r.label, r.unit, r.address,
                                   r.processCount, r.errorCount, ratio))

    def help_stats(self):
        self.__println("Usage: stats")
        self.__println("-----------")
        self.__println("List the statistics of configured datapoints")



    def do_change(self, arg):
        (idx, key, typ, value) = self.splitterRe.split(arg)
        try:
            i = int(idx)
            r = self.registers[i]

            if typ == 'I':
                value = parseIntArbitraryBase(value)
            elif typ == 'F':
                value = float(value)
            elif typ == 'B':
                if value in ['true', 'True', 'yes', 'Yes']:
                    value = True
                elif value in ['false', 'False', 'no', 'No']:
                    value = False
                else:
                    raise CmdInterpreterException('boolean value must be true or false, yes or no')
            elif typ == 'S':
                # string
                pass
            elif typ == 'T':
                value = datetime.timedelta(seconds=float(value))
            elif typ == 'N':
                value = None
            else:
                raise CmdInterpreterException('unknown type specifier, must be I, F, B, S or T')
            
            if key not in r.__dict__:
                raise CmdInterpreterException('selected datapoint does not support key')
            
            r.__dict__[key] = value
        except ValueError as e:
            self.__println("ERROR: {0!s}, {1!s}".format(e.__class__.__name__, e))

    def help_change(self):
        self.__println("Usage: change <idx> <key> <type> <value>")
        self.__println("Changes on attribute of a datapoint")
        self.__println("DO NOT FORGET TO SAVE AFTERWARDS!")
        self.__println("---------------------------------------------------------------------")
        self.__println("<idx>                      Index, use list command to find")
        self.__println("<key>                      Name of attribute")
        self.__println("<type>                     Type of attribute")
        self.__println("                           I .. Integer")
        self.__println("                           F .. Float")
        self.__println("                           B .. Boolean")
        self.__println("                           T .. Timedelta, give in seconds")
        self.__println("                           S .. String")
        self.__println("                           N .. None (Value must be given but is not")
        self.__println("                                      considered)")
        self.__println("<value>                    New value")




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
        self.__println("DO NOT FORGET TO SAVE AFTERWARDS!")

    def do_save(self, arg):
        RegisterDatapoint.saveRegisterList(self.registers, self.config.registerFile)

    def help_save(self):
        self.__println("Usage: save")
        self.__println("Saves a modified register list into the register file.")

    def do_load(self, arg):
        try:
            registers = RegisterDatapoint.loadRegisterList(self.config.registerFile)
            self.registers = registers
        except Exception as e:
            self.__println("Unable to load register list: {0!s}".format(e))

    def help_load(self):
        self.__println("Usage: load")
        self.__println("Reload the register file, overwrite all unsaved changes.")



class CmdHandle(socketserver.StreamRequestHandler):
    def handle(self):
        logger = logging.getLogger('CmdHandle')
        cmd = CmdInterpreter(io.TextIOWrapper(self.rfile), io.TextIOWrapper(self.wfile), self.server.userData.config, 
                             self.server.userData.notifier, self.server.userData.registers)
        try:
            cmd.cmdloop()
            logger.info("Cmd handle terminated")
        except ConnectionAbortedError as e:
            logger.info("Cmd handle externally interrupted")

class MyThreadingTCPServer(socketserver.ThreadingTCPServer):
    def __init__(self, host, handler, userData):
        super().__init__(host, handler)
        self.userData = userData

class MyCmdUserData(object):
    def __init__(self, config, notifier, registers):
        self.config = config
        self.notifier = notifier
        self.registers = registers

class CmdServer(threading.Thread):
    def __init__(self, config, notifier, registers):
        super().__init__()
        self.config = config
        self.server = MyThreadingTCPServer((config.cmdAddress, config.cmdPort), CmdHandle, MyCmdUserData(config, notifier, registers))
        self.daemon = True

    def start(self):
        self.server.serve_forever()


