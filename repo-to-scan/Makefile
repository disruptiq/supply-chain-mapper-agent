# Sample Makefile for testing

CC = gcc
CFLAGS = -Wall -I/usr/include/mysql -I/usr/local/include
LDFLAGS = -L/usr/local/lib
LIBS = -lmysqlclient -lm -lcurl -lssl -lcrypto

# Pkg-config dependencies
GTK_CFLAGS = $(shell pkg-config --cflags gtk+-3.0)
GTK_LIBS = $(shell pkg-config --libs gtk+-3.0)

.PHONY: all clean

all: myprogram

myprogram: main.o utils.o
	$(CC) $(LDFLAGS) -o $@ $^ $(LIBS) $(GTK_LIBS)

main.o: main.c
	$(CC) $(CFLAGS) $(GTK_CFLAGS) -c $<

utils.o: utils.c
	$(CC) $(CFLAGS) -c $<

clean:
	rm -f *.o myprogram
