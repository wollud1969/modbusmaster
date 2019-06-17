#include <unistd.h>
#include <termios.h>
#include <sys/ioctl.h>
#include <stdio.h>
#include <linux/serial.h>
#include <errno.h>
#include <string.h>
#include <stdint.h>
#include <bcm2835.h>


const uint8_t DE_PIN = RPI_V2_GPIO_P1_11;

int set_rs485_mode(int fd) {
  bcm2835_init();
  bcm2835_gpio_fsel(DE_PIN, BCM2835_GPIO_FSEL_OUTP);
  bcm2835_gpio_write(DE_PIN, LOW);
}

ssize_t writec(int fd, char *buf, size_t count) {
  bcm2835_gpio_write(DE_PIN, LOW);
  ssize_t r = write(fd, buf, count);
  uint8_t lsr;
  do {
    int r = ioctl(fd, TIOCSERGETLSR, &lsr);
  } while (!(lsr & TIOCSER_TEMT));
  bcm2835_gpio_write(DE_PIN, HIGH);

  return r;
}

