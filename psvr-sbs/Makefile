CC ?= cc
PKG_CONFIG ?= pkg-config
CFLAGS += -O2 -Wall -Wextra -std=c11 $(shell $(PKG_CONFIG) --cflags x11 xrandr xext)
LDLIBS += $(shell $(PKG_CONFIG) --libs x11 xrandr xext)

psvr-sbs: main.c
	$(CC) $(CFLAGS) -o $@ main.c $(LDLIBS)

.PHONY: clean
clean:
	rm -f psvr-sbs
