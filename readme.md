# modbusmaster

## Disable Bluetooth on RPi3

Add at the end of `/boot/config`:

    dtoverlay=pi3-disable-bt

Remove mentions of `serial0` from `/boot/cmdline`.


## Enable rs485 mode

Use the submodule rpirtscts to enable to alternate functions of the related
pins at the RPi MCU. It is submoduled here, can be found directly at https://github.com/mholling/rpirtscts

    cd rpirtscts
    gcc -o rpirtscts rpirtscts.c
    sudo ./rpirtscts on

This needs to be done at every boot.

Kudos to danjperron, cmp. (https://www.raspberrypi.org/forums/viewtopic.php?f=98&t=224533&hilit=rs+485#p1383709)


## Pinout

Find a good pinout diagram at (https://raw.githubusercontent.com/ppelleti/hs-wiringPi/master/pin-diagram.png).

TX is at GPIO14, RX is at GPIO15 and RTS (control line for transmitter enable) is at GPIO17.


## Python snippet to test

    import serial.rs485
    ser=serial.rs485.RS485(port='/dev/ttyAMA0',baudrate=9600)
    ser.rs485_mode = serial.rs485.RS485Settings(False,True)
    ser.write('a test'.encode('utf-8'))


