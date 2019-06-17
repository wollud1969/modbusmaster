#include <unistd.h>
#include <sys/ioctl.h>
#include <stdint.h>
#include <wiringPi.h>


const uint8_t DE_PIN = 0;

int init() {
  wiringPiSetup();
  pinMode(DE_PIN, OUTPUT);
  digitalWrite(DE_PIN, LOW);
}

ssize_t writec(int fd, char *buf, size_t count) {
  digitalWrite(DE_PIN, HIGH);
  ssize_t r = write(fd, buf, count);
  uint8_t lsr;
  do {
    int r = ioctl(fd, TIOCSERGETLSR, &lsr);
  } while (!(lsr & TIOCSER_TEMT));
  digitalWrite(DE_PIN, LOW);

  return r;
}

