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
from dominion.game.socketio_base import get_message

# TODO: move this somewhere central
def get_available_cards(state, max_cost=50):
    cardstacks = [(get_card_from_name(c[0]), c[0], c[1])
            for c in state['cardstacks']]
    available_cards = [c[1] for c in cardstacks
            if c[0].cost() <= max_cost and c[2] > 0]
    return available_cards

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
        hand = [get_card_from_name(c[0], c[1]) for c in hand]
        actions = [c for c in hand if c._is_action]
        coin = sum([c.coins() for c in hand])
        available_cards = get_available_cards(state, coin)
        if actions:
            action = self.r.choice(actions)
            print 'playing action', action.cardname
            ws.send({'playaction': action._card_num})
            hand.remove(action)
            while action.requires_response():
                message = get_message(ws)
                self.handle_action(state, hand, message, ws)
        if available_cards:
            to_buy = self.r.choice(available_cards)
            print 'buying', to_buy
            ws.send({'buycard': to_buy})
        ws.send({'endturn': 'end turn'})

    def handle_action(self, state, hand, message, ws):
        if 'user-action' in message:
            action = message['user-action']
            if 'gain-card-' in action:
                max_cost = int(action.split('-')[-1])
                available_cards = get_available_cards(state, max_cost)
                gained = self.r.choice(available_cards)
                ws.send({'gained': gained})
            if action == 'trash-one':
                trashed = self.r.choice(hand)
                ws.send({'trashed': trashed})


if __name__ == "__main__":
    import sys
    player = 0
    a = Agent(player)
    a.connect("ws://localhost:9000/socket.io/websocket")


# vim: et sw=4 sts=4
