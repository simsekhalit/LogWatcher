#!/usr/bin/env python3
import cmd
import re
import socket
import threading
from util import SocketBuffer


class LogWatchClient(threading.Thread):
    def __init__(self):
        super(LogWatchClient, self).__init__()
        filteredLogs = {}


class ClientLoop(cmd.Cmd):
    def __init__(self):
        super(ClientLoop, self).__init__()
        self.prompt = "> "
        self.intro = "Available commands are setMatch, combineMatch, delMatch"
        self.server = ("localhost", 2470)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(self.server)
        self.buffer = SocketBuffer(self.sock)
        self.logs = {}
        self.respondCV = threading.Condition()
        self.respond = ""
        self.sockLock = threading.Lock()
        self.receiver = threading.Thread(target=self.receive_logs)
        self.receiver.start()

    def receive_logs(self):
        header = self.buffer.read()
        while header:
            if header == "log":
                lwId = int(self.buffer.read())
                data = self.buffer.read()
                self.logs[int(lwId)].append(data)
            elif header == "respond":
                respond = self.buffer.read()
                with self.respondCV:
                    self.respond = respond
                    self.respondCV.notify()
            else:
                pass
            header = self.buffer.read()

    def get_respond(self):
        with self.respondCV:
            self.respondCV.wait()
        return self.respond

    def emptyline(self):
        pass

    def do_create(self, args):
        self.buffer.write("create")
        print(self.get_respond())

    def do_list(self, args):
        self.buffer.write("list")
        print(self.get_respond().replace(".", "\n"))

    def do_register(self, args):
        if args.isdigit():
            self.buffer.write("register\n" + args)
            print(self.get_respond())
        else:
            print("Invalid command")

    def do_unregister(self, args):
        if args.isdigit():
            self.buffer.write("unregister\n" + args)
            print(self.get_respond())
        else:
            print("Invalid command")

    def do_setMatch(self, args):
        args = args.split(' ')
        lwId = args[0]
        args = "".join(args[1:])
        args = re.search("(\(.*\)) (\(.*\))", args)
        if not args:
            print("Invalid Command")
            return
        match = args.group(1)
        address = args.group(2)
        self.buffer.write("setMatch\n" + match + "\n" + address)
        with self.respondCV:
            self.respondCV.wait()
        print(self.respond)

    def do_EOF(self, arg):
        print()
        exit(0)


if __name__ == "__main__":
    ClientLoop().cmdloop()
