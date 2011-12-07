#!/usr/bin/env python

import websocket
import thread
import time
import asyncore
from random import Random


class Agent(object):
    def __init__(self, player):
        self.available_player = player
        self.r = Random()

    def connect(self, url):
        ws = websocket.WebSocket(url,
                onopen=self.on_open,
                onmessage=self.on_message,
                onclose=self.on_close)
        try:
            asyncore.loop()
        except KeyboardInterrupt:
            ws.close()

    def on_message(self, ws, message):
        print 'Message:', message
        if 'available' in message:
            self.player = message['available'][self.available_player]
            ws.send({'player': self.player})
        if 'count' in message:
            # We have to be careful here, because the server doesn't handle
            # concurrent messages very well.
            if message.get('current_player', None) == self.player:
                print 'Incrementing count to', message['count'] + 1
                ws.send({'val': message['count'] + 1})

    def on_close(self, ws):
        print "### closed ###"

    def on_open(self, ws):
        print 'Connection opened'
        ws.send({'game': 1})


if __name__ == "__main__":
    import sys
    player = 0
    a = Agent(player)
    a.connect("ws://localhost:9000/socket.io/websocket")


# vim: et sw=4 sts=4
