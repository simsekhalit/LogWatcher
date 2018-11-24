#!/usr/bin/env python3


class AddressNotFoundError(Exception):
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
    def getNode(self, address = ()):
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
