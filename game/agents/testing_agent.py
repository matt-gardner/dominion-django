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

    # This isn't optimal, but because of the way this websocket client code
    # works, we have to end every method here with a send.  The server
    # acknowledges every send that you do with something, and it tells you the
    # game state so you can pick up where you left off.  You might need to
    # remember things in your code, though, if you want to make correct
    # decisions.
    def on_message(self, ws, message):
        print 'Message:', message
        if 'available' in message:
            self.player = message['available'][self.available_player]
            ws.send({'player': self.player})
        elif (('newturn' in message or 'connected' in message) and
                message['game-state']['current_player'] == self.player):
            ws.send({'myturn': 'info please'})
        elif 'yourturn' in message:
            player_state = message['player-state']
            game_state = message['game-state']
            self.take_turn(ws, player_state, game_state)
        elif 'action-finished' in message:
            self.take_turn(ws, self.player_state, self.game_state)
        elif 'card-bought' in message:
            self.take_turn(ws, self.player_state, self.game_state)
        elif 'user-action' in message:
            attack = message.get('attacking-player', None)
            self.handle_action(ws, message, attack)
        elif 'attack-response' in message:
            if message['attacking-player'] == self.player:
                # Sadly, it seems this convoluted approach is the only way to
                # get the message to go to the right socket on the server.
                print 'Forwarding attack response to server'
                ws.send(message)
        elif 'connected' in message:
            pass
        elif 'newturn' in message:
            pass
        else:
            print "Didn't know how to handle the last message"

    def on_close(self, ws):
        print "### closed ###"

    def on_open(self, ws):
        print 'Connection opened'
        ws.send({'game': 1})

    def take_turn(self, ws, player_state, game_state):
        # We save these here for future use, because this code has to be event
        # driven.
        self.player_state = player_state
        self.game_state = game_state
        if player_state['num-actions'] > 0:
            self.play_action(ws, player_state, game_state)
        elif player_state['num-buys'] > 0:
            self.buy_card(ws, player_state, game_state)
        else:
            ws.send({'endturn': 'end turn'})

    def play_action(self, ws, player_state, game_state):
        hand = [get_card_from_name(c[0], c[1]) for c in player_state['hand']]
        actions = [c for c in hand if c._is_action]
        coin = sum([c.coins() for c in hand])
        if actions:
            action = self.r.choice(actions)
            to_remove = [action.cardname, action._card_num]
            print 'playing action', action.cardname
            player_state['hand'].remove(to_remove)
            player_state['num-actions'] -= 1
            # This line may not be necessary, but just in case...
            self.player_state = player_state
            ws.send({'playaction': action._card_num})
        else:
            self.buy_card(ws, player_state, game_state)

    def buy_card(self, ws, player_state, game_state):
        hand = [get_card_from_name(c[0], c[1]) for c in player_state['hand']]
        coin = sum([c.coins() for c in hand])
        available_cards = get_available_cards(game_state, coin)
        if available_cards and player_state['num-buys'] > 0:
            to_buy = self.r.choice(available_cards)
            print 'buying', to_buy
            player_state['num-buys'] -= 1
            # This line may not be necessary, but just in case...
            self.player_state = player_state
            ws.send({'buycard': to_buy})
        else:
            ws.send({'endturn': 'end turn'})

    def handle_action(self, ws, received_message, attack):
        game_state = self.game_state
        hand = self.player_state['hand']
        cards_in_hand = [get_card_from_name(c[0], c[1])
                for c in self.player_state['hand']]
        message = {}
        # This is because attack actions need to know the player that is
        # responding, and because attack responses need to be forwarded by the
        # server.
        if attacking_player:
            message['responding-player'] = self.player
            message['attacking-player'] = attacking_player
            message['attack-response'] = 'pues!'
        action = received_message['user-action']
        if 'gain-card-' in action:
            max_cost = int(action.split('-')[-1])
            available_cards = get_available_cards(game_state, max_cost)
            gained = self.r.choice(available_cards)
            message['gained'] = gained
            ws.send(message)
        elif 'gain-treasure-' in action:
            max_cost = int(action.split('-')[-1])
            # TODO: we need some checking in here, to make sure these cards are
            # available
            if max_cost == 3:
                message['gained'] = 'Silver'
            if max_cost == 6:
                message['gained'] = 'Gold'
            if max_cost == 9:
                message['gained'] = 'Platinum'
            message['gained'] = gained
            ws.send(message)
        elif action == 'trash-one':
            trashed = self.r.choice(hand)
            self.player_state['hand'].remove(trashed)
            message['trashed'] = trashed[1]
            ws.send(message)
        elif action == 'trash-any':
            message['trashed'] = []
            ws.send(message)
        elif action == 'trash-treasure':
            treasure = [c for c in cards_in_hand if c._is_treasure]
            trashed = self.r.choice(treasure)
            to_remove = [trashed.cardname, trashed._card_num]
            self.player_state['hand'].remove(to_remove)
            message['trashed'] = trashed._card_num
            ws.send(message)
        elif action == 'pick-action':
            actions = [c for c in cards_in_hand if c._is_action]
            message['gained'] = self.r.choice(actions).card_num
            ws.send(message)
        elif action == 'library-keep-card':
            message['keep'] = 'yes'
            ws.send(message)
        elif action == 'discard-any':
            message['discarded'] = []
            ws.send(message)
        elif action == 'discard-two':
            discarded = self.hand[:2]
            for d in discarded:
                self.player_state['hand'].remove(d)
            message['discarded'] = [d[1] for d in discarded]
            ws.send(message)
        elif action == 'discard-to-three':
            discarded = self.player_state['hand'][3:]
            for d in discarded:
                self.player_state['hand'].remove(d)
            message['discarded'] = [d[1] for d in discarded]
            print 'sending message:', message
            ws.send(message)
        elif action == 'chancellor':
            message['reshuffle'] = 'yes'
            ws.send(message)
        elif action == 'gain-curse':
            message['ok'] = 'curse you!'
            ws.send(message)
        elif action == 'spy':
            message['ok'] = 'treacherous lout!'
            ws.send(message)
        elif action == 'thief':
            message['ok'] = 'thieving scum!'
            ws.send(message)
        elif action == 'spying':
            message['discard'] = 'yes'
            ws.send(message)
        elif action == 'stealing':
            message['trash'] = received_message['cards'][0][1]
            ws.send(message)
        elif action == 'bureaucrat-attacking':
            victory_cards = [c for c in cards_in_hand if c._is_victory]
            if not victory_cards:
                message['victory-card'] = -1
            else:
                message['victory-card'] = victory_cards[0]._card_num
            ws.send(message)
        else:
            raise ValueError("I don't know how to respond to this action: %s"
                    % action)


if __name__ == "__main__":
    import sys
    player = 0
    a = Agent(player)
    a.connect("ws://localhost:9000/socket.io/websocket")


# vim: et sw=4 sts=4
