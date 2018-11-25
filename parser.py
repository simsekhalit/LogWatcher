from pyparsing import Word, alphas, Suppress, Combine, nums, string, Optional, Regex
import time


class Parser(object):
    def __init__(self):
        ints = Word(nums)

        # timestamp
        month = Word(string.ascii_uppercase, string.ascii_lowercase, exact=3)
        day   = ints
        hour  = Combine(ints + ":" + ints + ":" + ints)

        timestamp = month + day + hour

        # hostname
        hostname = Word(alphas + nums + "_" + "-" + ".")

        # appname
        appname = Word(alphas + "/" + "-" + "_" + ".") + Optional(Suppress("[") + ints + Suppress("]")) + Suppress(":")

        # message
        message = Regex(".*")

        # pattern build
        self.__pattern = timestamp + hostname + appname + message

    def parse(self, line):
        parsed = self.__pattern.parseString(line)

        payload              = {}
        payload["timestamp"] = int(time.mktime(time.strptime(str(time.localtime().tm_year) + " " + ' '.join(parsed[:3]),
                                                             "%Y %b %d %H:%M:%S")))
        payload["hostname"]  = parsed[3]
        payload["appname"]   = parsed[4]
        if len(parsed) == 7:
            payload["pid"]       = parsed[5]
        payload["message"]   = parsed[-1]

        return payload
