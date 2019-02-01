#!/usr/bin/env python3

import log_parser
import multiprocessing
import socket
import threading

collectorPort = 5140
databasePath = "db.sqlite3"
UDSAddr = "UDS"


def createNode(value: tuple = (), left: dict = None, right: dict = None):
    return {"value": value, "left": left, "right": right}


# Return node at given address
def getNode(rules: dict, address: tuple):
    if address == ():
        return rules
    else:
        node = rules
        for step in address:
            if step == 0:
                if node["left"]:
                    node = node["left"]
                else:
                    raise Exception("Could not find node at given address:", address)
            elif step == 1:
                if node["right"]:
                    node = node["right"]
                else:
                    raise Exception("Could not find node at given address:", address)
            else:
                raise Exception("Invalid address:", address)
        return node


class LogCollector(multiprocessing.Process):
    def __init__(self, hostAddress, port, pipe):
        super(LogCollector, self).__init__(daemon=True)
        self.hostAddress = hostAddress
        self.port = port
        self.pipe = pipe

    def run(self):
        logParser = log_parser.Parser(True)
        collectorSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        collectorSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        collectorSock.bind((self.hostAddress, self.port))

        try:
            while True:
                data, addr = collectorSock.recvfrom(4096)
                payload = logParser.parse(data.decode().rstrip())
                self.pipe.send(payload)
        except KeyboardInterrupt:
            exit()


class LogWatchTracker:
    def __init__(self, process, pipe):
        self.process = process
        self.pipe = pipe
        self.lock = threading.Lock()


class SocketBuffer:
    def __init__(self, sock, addr):
        self.sock = sock
        self.addr = addr

    def close(self):
        self.sock.close()

    def recv(self):
        return self.sock.recv(4096).decode().rstrip()

    def read(self):
        return self.sock.recv(4096).decode().rstrip().split("\n")

    def send(self, data):
        self.sock.send(data.rstrip().encode())

    def write(self, data):
        self.sock.send("\n".join(data).encode())
