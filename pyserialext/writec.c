#include <unistd.h>
#include <termios.h>
#include <sys/ioctl.h>
#include <stdio.h>
#include <linux/serial.h>
#include <errno.h>
#include <string.h>
#include <stdint.h>
#include <wiringPi.h>


const uint8_t DE_PIN = 0;

int set_rs485_mode(int fd) {
  wiringPiSetup();
  pinMode(DE_PIN, OUTPUT);
  digitalWrite(DE_PIN, HIGH);
}

ssize_t writec(int fd, char *buf, size_t count) {
  digitalWrite(DE_PIN, LOW);
  ssize_t r = write(fd, buf, count);
  uint8_t lsr;
  do {
    int r = ioctl(fd, TIOCSERGETLSR, &lsr);
  } while (!(lsr & TIOCSER_TEMT));
  digitalWrite(DE_PIN, HIGH);

  return r;
}

