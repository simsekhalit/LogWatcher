#!/usr/bin/env python3

import time
import sys
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server = ("localhost",5140)

with open("samples/sample.log", "br") as log_source:
    log = log_source.readline()

    while log:
        sock.sendto(log,server)
        # time.sleep(0.1)
        log = log_source.readline()
