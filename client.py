#!/usr/bin/env python3
import cmd
import os
import re
import socket
import threading


class ClientLoop(cmd.Cmd):
    def __init__(self):
        super(ClientLoop, self).__init__()
        self.prompt = "> "
        self.intro = "Please type help to see available commands."
        self.server = ("localhost", 2470)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(self.server)
        self.logs = {}
        self.respondCV = threading.Condition()
        self.respond = None
        self.sockLock = threading.Lock()
        self.receiver = threading.Thread(target=self.receive_logs, daemon=True)
        self.receiver.start()

    def read(self):
        return self.sock.recv(4096).decode()

    def write(self, data):
        self.sock.sendall(data.encode())

    def receive_logs(self):
        data = self.read().split("\n")
        while data[0]:
            if data[0] == "log":
                lwId = int(data[1])
                log = data[2]
                self.logs[lwId].append(log)
            elif data[0] == "respond":
                respond = "\n".join(data[1:])
                with self.respondCV:
                    self.respond = respond
                    self.respondCV.notify()
            else:
                pass
            data = self.read().split("\n")

        print("Server shutdown.")
        exit(0)

    def get_respond(self):
        with self.respondCV:
            self.respondCV.wait()
        return self.respond

    def emptyline(self):
        pass

    def do_create(self, args):
        self.write("create")
        print(self.get_respond())

    def do_list(self, args):
        self.write("list")
        print(self.get_respond())

    def do_register(self, args):
        if args.isdigit():
            self.write("register\n" + args)
            print(self.get_respond())
        else:
            print("Invalid command")

    def do_unregister(self, args):
        if args.isdigit():
            self.write("unregister\n" + args)
            print(self.get_respond())
        else:
            print("Invalid command")

    def do_printRules(self, args):
        if args.isdigit():
            self.write("printRules\n" + args)
            print(self.get_respond())
        else:
            print("Invalid command")

    def do_setMatch(self, args):
        args = re.search("(\d+) (\(.*\)) (\(.*\))", args)
        if not args:
            print("Invalid Command")
            return
        lwId = args.group(1)
        match = args.group(2)
        address = args.group(3)
        self.write("setMatch\n" + lwId + "\n" + match + "\n" + address)
        print(self.get_respond())

    def do_combineMatch(self, args):
        args = re.search("(\d+) (\(.*\)) (AND|OR) (\(.*\))", args)
        if not args:
            print("Invalid Command")
            return
        lwId = args.group(1)
        match = args.group(2)
        connector = args.group(3)
        address = args.group(4)
        self.write("combineMatch\n" + lwId + "\n" + match + "\n" + connector + "\n" + address)
        print(self.get_respond())

    def do_delMatch(self, args):
        args = re.search("(\d+) (\(.*\))", args)
        if not args:
            print("Invalid Command")
            return
        lwId = args.group(1)
        address = args.group(2)
        self.write("delMatch\n" + lwId + "\n" + address)
        print(self.get_respond())

    def do_save(self, args):
        if args.isdigit():
            self.write("save\n" + args)
            print(self.get_respond())
        else:
            print("Invalid command")

    def do_load(self, args):
        if args.isdigit():
            self.write("load\n" + args)
            print(self.get_respond())
        else:
            print("Invalid command")

    def do_EOF(self, arg):
        print()
        exit(0)


if __name__ == "__main__":
    ClientLoop().cmdloop()
