#!/usr/bin/env python


def get_message(socketio):
    message = socketio.recv()
    if not socketio.connected():
        raise ConnectionLostError()
    if not (len(message) == 1 and type(message) == list):
        raise ValueError("Message wasn't a list of 1 item")
    print 'Message received:', message[0]
    return message[0]

# vim: et sw=4 sts=4
