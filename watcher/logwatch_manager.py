#!/usr/bin/env python3
from ast import literal_eval
import multiprocessing
import os
import selectors
import socket
import sqlite3
import sys
import threading
from logwatch import LogWatch
from util import collectorPort, databasePath, UDSAddr, createNode, LogCollector, LogWatchTracker, SocketBuffer


class LogWatchManager:
    def __init__(self):
        self.logWatchTrackers = {}
        self.logWatchTrackersLock = threading.Lock()
        self.hostAddress = "localhost"
        self.selector = selectors.DefaultSelector()

    def start(self):
        self.initWatchers()
        self.startLogCollector()
        self.startServer()
        self.run()

    def run(self):
        try:
            while True:
                events = self.selector.select()
                for key, _ in events:
                    # collectorPipe
                    if key.data == 0:
                        payload = key.fileobj.recv()
                        with self.logWatchTrackersLock:
                            for lw in self.logWatchTrackers.values():
                                with lw.lock:
                                    lw.pipe.send(("log", payload))

                    # serverPipe: New client is connected.
                    elif key.data == 1:
                        sock, addr = key.fileobj.accept()
                        thread = threading.Thread(target=self.clientHandler, args=(sock, addr), daemon=True)
                        thread.start()

                    # LogWatch pipe
                    else:
                        pass
        except KeyboardInterrupt:
            exit()

    def clientHandler(self, sock, addr):
        methodsTable = {"create": self.createWatcher, "setMatch": self.setMatch, "combineMatch": self.combineMatch,
                        "delMatch": self.delMatch}

        buffer = SocketBuffer(sock, addr)
        data = buffer.read()
        try:
            if not data:
                return
            ret = methodsTable[data[0]](*data[1:])
            buffer.send(ret)
        except BaseException as e:
            buffer.send("2")
            print("Log Watch Manager ({}): {} ({})".format(addr, e, data))
            raise e
        finally:
            buffer.close()

    def createWatcher(self, lwID=None, name=None, soft=False):
        with self.logWatchTrackersLock:
            if not lwID:
                lwID = len(self.logWatchTrackers)
            if not name:
                name = "Watcher {}".format(lwID)
            if not soft:
                with sqlite3.connect(databasePath) as conn:
                    c = conn.cursor()
                    c.execute("""insert into watchers values (?, ?);""", (lwID, name))
                    c.execute("""insert into rules values(?, ?)""", (lwID, str(createNode())))
                print("{} created.".format(name), file=sys.stderr)
            parent_conn, child_conn = multiprocessing.Pipe()
            process = LogWatch(lwID, name, child_conn)
            lwTracker = LogWatchTracker(process, parent_conn)
            self.logWatchTrackers[lwID] = lwTracker
            self.selector.register(parent_conn, selectors.EVENT_READ, lwTracker)
        process.start()
        print("{} started.".format(name), file=sys.stderr)
        return "0"

    def setMatch(self, lwID, match, address):
        lwID = int(lwID)
        match = literal_eval(match)
        address = literal_eval(address)
        with self.logWatchTrackersLock:
            lw = self.logWatchTrackers[lwID]
        with lw.lock:
            lw.pipe.send(("setMatch", match, address))
            response = lw.pipe.recv()
        return response

    def combineMatch(self, lwID, match, connector, address):
        lwID = int(lwID)
        match = literal_eval(match)
        connector = connector
        address = literal_eval(address)
        with self.logWatchTrackersLock:
            lw = self.logWatchTrackers[lwID]
        with lw.lock:
            lw.pipe.send(("combineMatch", match, connector, address))
            response = lw.pipe.recv()
        return response

    def delMatch(self, lwID, address):
        lwID = int(lwID)
        address = literal_eval(address)
        with self.logWatchTrackersLock:
            lw = self.logWatchTrackers[lwID]
        with lw.lock:
            lw.pipe.send(("delMatch", address))
            response = lw.pipe.recv()
        return response

    def initWatchers(self):
        with sqlite3.connect(databasePath) as conn:
            c = conn.cursor()
            c.execute("""CREATE TABLE IF NOT EXISTS watchers
            (wid INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, name TEXT)""")
            c.execute("""CREATE TABLE IF NOT EXISTS rules (wid INTEGER NOT NULL PRIMARY KEY, rules TEXT NOT NULL)""")
            c.execute("""CREATE TABLE IF NOT EXISTS logs
            (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, wid INTEGER NOT NULL, log TEXT NOT NULL)""")
            watchers = c.execute("""select wid, name from watchers""").fetchall()

        for watcher in watchers:
            self.createWatcher(watcher[0], watcher[1], soft=True)

    def startLogCollector(self):
        collectorPipe, externalPipe = multiprocessing.Pipe()
        collector = LogCollector(self.hostAddress, collectorPort, externalPipe)
        collector.start()
        self.selector.register(collectorPipe, selectors.EVENT_READ, 0)

    def startServer(self):
        if os.path.exists(UDSAddr):
            os.unlink(UDSAddr)

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(UDSAddr)
        sock.listen(10)
        self.selector.register(sock, selectors.EVENT_READ, 1)


if __name__ == "__main__":
    lwm = LogWatchManager()
    lwm.start()
