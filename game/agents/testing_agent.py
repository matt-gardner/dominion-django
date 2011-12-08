#!/usr/bin/env python

import os, sys

print os.getcwd()+'/..'
sys.path.append(os.getcwd()+'/..')
os.environ['DJANGO_SETTINGS_MODULE'] = 'dominion.settings'

import websocket
import thread
import time
import asyncore
from random import Random
from dominion.game.models import get_card_from_name

# We have to be careful in our message passing, because the server doesn't
# handle concurrent messages very well.

class Agent(object):
    def __init__(self, player):
        self.available_player = player
        self.player = None
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
        if (('newturn' in message or 'connected' in message) and
                message['state']['current_player'] == self.player):
            ws.send({'myturn': 'info please'})
        if 'yourturn' in message:
            hand = message['hand']
            state = message['state']
            self.take_turn(ws, hand, state)

    def on_close(self, ws):
        print "### closed ###"

    def on_open(self, ws):
        print 'Connection opened'
        ws.send({'game': 1})

    def take_turn(self, ws, hand, state):
        cards = [get_card_from_name(c[0], c[1]) for c in hand]
        actions = [c for c in cards if c._is_action]
        coin = sum([c.coins() for c in cards])
        cardstacks = [(get_card_from_name(c[0]), c[0], c[1])
                for c in state['cardstacks']]
        available_cards = [c[1] for c in cardstacks
                if c[0].cost() <= coin and c[2] > 0]
        if actions:
            action = self.r.choice(actions)
            print 'playing action', action.cardname
            ws.send({'playaction': action._card_num})
        if available_cards:
            to_buy = self.r.choice(available_cards)
            print 'buying', to_buy
            ws.send({'buycard': to_buy})
        ws.send({'endturn': 'end turn'})


if __name__ == "__main__":
    import sys
    player = 0
    a = Agent(player)
    a.connect("ws://localhost:9000/socket.io/websocket")


# vim: et sw=4 sts=4
