#!/usr/bin/env python

import websocket
import thread
import time
import asyncore

def on_message(ws, message):
    print 'Message:', message
    if 'available' in message:
        ws.send({'player': message['available'][0]})
    if 'count' in message:
        ws.send({'val': message['count'] + 1})


def on_close(ws):
    print "### closed ###"


def on_open(ws):
    print 'Connection opened'
    ws.send({'game': 1})


if __name__ == "__main__":
    ws = websocket.WebSocket("ws://localhost:9000/socket.io/websocket",
            onopen=on_open,
            onmessage=on_message,
            onclose=on_close)

    try:
        asyncore.loop()
    except KeyboardInterrupt:
        ws.close()

# vim: et sw=4 sts=4
