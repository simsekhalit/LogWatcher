#!/usr/bin/env python3
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

    def load(self, dict_):
        if type(dict_["value"]) == list:
            self.value = tuple(dict_["value"])
        else:
            self.value = dict_["value"]
        if dict_["left"]:
            self.left = Node().load(dict_["left"])
        if dict_["right"]:
            self.right = Node().load(dict_["right"])
        return self


class LogCollector(multiprocessing.Process):
    def __init__(self, hostAddress, port, pipe):
        super(LogCollector, self).__init__()
        self.hostAddress = hostAddress
        self.port = port
        self.pipe = pipe

    def run(self):
        logParser = parser.Parser(True)
        collectorSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
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
        self.buffer = sock.makefile("brw")

    def read(self):
        return self.buffer.readline().decode()[:-1]

    def write(self, data):
        self.buffer.write(data.encode() + b"\n")
        self.buffer.flush()


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

# class Observer:
#     """Represents an observer(user) of a Logwatch object
#     """
#     def __init__(self, watcher):
#         self.filteredLogs = []
#         watcher.register(self)
#
#     def update(self, log):
#         self.filteredLogs.append(log)
