#!/usr/bin/env python3
from ast import literal_eval
import multiprocessing
import socket
import threading
import parser


class AddressNotFoundError(Exception):
    pass


class NotAnObserverError(Exception):
    pass


class Node(dict):
    """Represents a binary tree node.
    """

    def __init__(self, value=None, left=None, right=None):
        super().__init__()
        self.__dict__ = self
        self.value = value
        self.left = left
        self.right = right

    # Return node at given address
    def getNode(self, address=()):
        if address == ():
            return self
        else:
            tmp = self
            for step in address:
                if step == 0:
                    if tmp.left is not None:
                        tmp = tmp.left
                    else:
                        raise AddressNotFoundError("Could not find node at given address:", address)
                elif step == 1:
                    if tmp.right is not None:
                        tmp = tmp.right
                    else:
                        raise AddressNotFoundError("Could not find node at given address:", address)
                else:
                    raise AddressNotFoundError("Invalid address:", address)
            return tmp

    def dump(self, path=()):
        ret = ((path, self.value), )
        if self.left:
            ret += self.left.dump(path + (0, ))
        if self.right:
            ret += self.right.dump(path + (1, ))
        return ret

    def load(self, dump):
        for row in dump:
            path = literal_eval(row[0])
            match = literal_eval(row[1])
            self.insert(path, match)

    def insert(self, path, match):
        road = path
        dst = self
        while road:
            if road[0] == 0:
                if dst.left is None:
                    dst.left = Node()
                dst = dst.left
            elif road[0] == 1:
                if dst.right is None:
                    dst.right = Node()
                dst = dst.right
            else:
                raise AddressNotFoundError("Invalid address:", path)
            road = road[1:]

        dst.value = match

    def loadJSON(self, dict_):
        if type(dict_["value"]) == list:
            self.value = tuple(dict_["value"])
        else:
            self.value = dict_["value"]
        if dict_["left"]:
            self.left = Node().loadJSON(dict_["left"])
        if dict_["right"]:
            self.right = Node().loadJSON(dict_["right"])
        return self


class LogCollector(multiprocessing.Process):
    def __init__(self, hostAddress, port, pipe):
        super(LogCollector, self).__init__(daemon=True)
        self.hostAddress = hostAddress
        self.port = port
        self.pipe = pipe

    def run(self):
        logParser = parser.Parser(True)
        collectorSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        collectorSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        collectorSock.bind((self.hostAddress, self.port))
        while True:
            data, addr = collectorSock.recvfrom(4096)
            payload = logParser.parse(data)
            self.pipe.send((addr, payload))


class LogWatchTracker:
    def __init__(self, process, pipe):
        self.process = process
        self.pipe = pipe
        self.logs = []
        self.lwLock = threading.Lock()
        self.registeredClients = []


class ClientTracker:
    def __init__(self, thread, sock):
        self.clientLock = threading.Lock()
        self.thread = thread
        self.sock = sock

    def read(self):
        return self.sock.recv(4096).decode()

    def write(self, data):
        self.sock.sendall(data.encode())


class SocketBuffer:
    def __init__(self, sock):
        self.buffer = sock.makefile("brw")
        self.sock = sock
        self.addr = sock.getpeername()

    def read(self):
        return self.buffer.readline().decode().rstrip()

    def write(self, data):
        self.buffer.write(data.encode() + b"\n")
        self.buffer.flush()
