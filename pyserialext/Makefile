CFLAGS=
LIBS=-lwiringPi

writec.so:	writec.o 
	$(LD) -shared $(LIBS) -o $@ $^

writec.o:	writec.c

.c.o:
	$(CC) $(CFLAGS) -c $<

.PHONY: clean
clean:
	-rm -f *.so *.o
