import RegisterDatapoint

registers = RegisterDatapoint.loadRegisterList('registers.json')

for r in registers:
    print("{0!s}".format(r))
