#!/usr/bin/env python3


class AddressNotFoundError(Exception):
    pass


class Node:
    """Represents a binary tree node.
    """

    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right

    def getNode(self, address):
        if address == ():
            return self
        else:
            temp = self
            for child in address:
                if temp.left is not None and temp.right is not None:  # current node is not a leaf (i.e. rule)
                    if child == 0:
                        temp = temp.left
                    else:
                        temp = temp.right
                else:
                    raise AddressNotFoundError("Could not find node at given address:", address)

            return temp
