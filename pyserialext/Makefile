CFLAGS=-I/opt/bcm2835/include

writec.so:	writec.o /opt/bcm2835/lib/libbcm2835.a
	$(LD) -shared -o $@ $^

writec.o:	writec.c

.c.o:
	$(CC) $(CFLAGS) -c $<

.PHONY: clean
clean:
	-rm -f *.so *.o
