#!/usr/bin/env python


def get_message(socketio):
    while True:
        message = socketio.recv()
        if not message:
            # Probably a heartbeat
            print 'Saw a heartbeart message'
            continue
        if not socketio.connected():
            raise ConnectionLostError()
        if not (len(message) == 1 and type(message) == list):
            print 'Bad message:', message
            raise ValueError("Message wasn't a list of 1 item")
        print 'Message received:', message[0]
        return message[0]

# vim: et sw=4 sts=4
