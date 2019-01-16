from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import os
import socket
import sqlite3
import sys

sys.path.insert(1, os.path.dirname(__file__,))
from watcher.util import databasePath, UDSAddr, SocketBuffer


@login_required
def index(request, create=None):
    """Home page which shows active Watcher instances."""
    if create:
        buffer = UDSBuffer()
        buffer.send("create")
        response = buffer.recv()
        if response == '0':
            return render(request, "index.html", {"watchers": getWatchers(), "create": "A new Logwatch instance successfully created."})
        else:
            return render(request, "index.html", {"watchers": getWatchers(), "create": "Failed to create a new Logwatch instance."})
    else:
        return render(request, "index.html", {"watchers": getWatchers()})


@login_required
def logs(request, lwID=None):
    """Shows filtered logs of corresponding Watcher instance."""
    # TODO: Check if lwID exists
    return render(request, "logs.html", {"logs": getLogs(lwID), "name": getWatcher(lwID)[0]})


@login_required
def rules(request, lwID=None):
    """Shows and updates rules of a Watcher instance."""
    if request.method == "GET":
        _rules = getRules(lwID)
        return render(request, "rules.html", {"rules": _rules, "name": getWatcher(lwID)[0]})
    elif request.POST['submit'] == 'SetMatch':
        path = request.POST['path']
        if path == 'NONE':
            path = '()'
        rule = request.POST['rule']
        buffer = UDSBuffer()
        buffer.send("setMatch\n" + lwID + "\n" + rule + "\n" + path)
        response = buffer.recv()
        _rules = getRules(lwID)
        if response == '0':
            return render(request, "rules.html", {"rules": _rules, "name": getWatcher(lwID)[0],
                                                  "op": "setMatch Operation was successful."})
        elif response == '2':
            return render(request, "rules.html", {"rules": _rules, "name": getWatcher(lwID)[0],
                                                  "op": "Please fill fields with correct types"})
        else:
            return render(request, "rules.html", {"rules": _rules, "name": getWatcher(lwID)[0],
                                                  "op": "setMatch Operation was not successful."})
    elif request.POST['submit'] == 'CombineMatch':
        path = request.POST['path']
        connector = request.POST['connector']
        if path == 'NONE':
            path = '()'
        rule = request.POST['rule']
        buffer = UDSBuffer()
        buffer.send("combineMatch\n" + lwID + "\n" + rule + "\n" + connector + "\n" + path)
        response = buffer.recv()
        _rules = getRules(lwID)
        if response == '0':
            return render(request, "rules.html", {"rules": _rules, "name": getWatcher(lwID)[0],
                                                  "op": "CombineMatch Operation was successful."})
        elif response == '2':
            return render(request, "rules.html", {"rules": _rules, "name": getWatcher(lwID)[0],
                                                  "op": "Please fill fields with correct types"})
        else:
            return render(request, "rules.html", {"rules": _rules, "name": getWatcher(lwID)[0],
                                                  "op": "CombineMatch Operation was not successful."})
    elif request.POST['submit'] == 'DelMatch':
        path = request.POST['path']
        if path == 'NONE':
            path = '()'
        buffer = UDSBuffer()
        buffer.send("delMatch\n" + lwID + "\n" + path)
        response = buffer.recv()
        _rules = getRules(lwID)
        if response == '0':
            return render(request, "rules.html", {"rules": _rules, "name": getWatcher(lwID)[0],
                                                  "op": "DelMatch Operation was successful."})
        elif response == '2':
            return render(request, "rules.html", {"rules": _rules, "name": getWatcher(lwID)[0],
                                                  "op": "Please fill fields with correct types"})
        else:
            return render(request, "rules.html", {"rules": _rules, "name": getWatcher(lwID)[0],
                                                  "op": "DelMatch Operation was not successful."})
    else:
        return render(request, 'error.html', {'message': 'Invalid request'})


def getLogs(lwID):
    with sqlite3.connect(os.path.join(os.path.dirname(__file__), databasePath)) as conn:
        c = conn.cursor()
        data = c.execute("""select log from logs where wid == ?""", (lwID,)).fetchall()
    return [log[0] for log in data]


def getRules(lwID):
    with sqlite3.connect(os.path.join(os.path.dirname(__file__), databasePath)) as conn:
        c = conn.cursor()
        return c.execute("""select rules from rules where wid == ?""", (lwID,)).fetchone()[0]


def getWatcher(lwID):
    with sqlite3.connect(os.path.join(os.path.dirname(__file__), databasePath)) as conn:
        c = conn.cursor()
        return c.execute("""select name from watchers where wid == ?""", (lwID,)).fetchone()


def getWatchers():
    ret = []
    with sqlite3.connect(os.path.join(os.path.dirname(__file__), databasePath)) as conn:
        c = conn.cursor()
        watchers = c.execute("""select wid, name from watchers""").fetchall()
        for watcher in watchers:
            logc = c.execute("""select count(log) from logs where wid == ?""", (watcher[0],)).fetchone()[0]
            rulec = getRules(watcher[0]).count("{'value': ")
            ret.append({"wid": watcher[0], "name": watcher[1], "rules": rulec, "logs": logc})
    return ret


def UDSBuffer():
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(os.path.join(os.path.dirname(__file__), UDSAddr))
    return SocketBuffer(sock, UDSAddr)
