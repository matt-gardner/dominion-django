#!/usr/bin/env python

import os, sys, httplib

print os.getcwd()+'/..'
sys.path.append(os.getcwd()+'/..')
os.environ['DJANGO_SETTINGS_MODULE'] = 'dominion.settings'

import websocket
from random import Random
from dominion.game.models import get_card_from_name
from dominion.game.socketio_base import get_message

# TODO: move this somewhere central
def get_available_cards(state, max_cost=50):
    cardstacks = [(get_card_from_name(c[0]), c[0], c[1])
            for c in state['cardstacks']]
    available_cards = [c[:2] for c in cardstacks
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
        conn  = httplib.HTTPConnection('localhost:9000')
        conn.request('POST','/socket.io/1/')
        resp  = conn.getresponse()
        resp_text = resp.read()
        print resp_text
        hskey = resp_text.split(':')[0]
        websocket.enableTrace(True)
        ws = websocket.WebSocketApp(url + 'websocket/' + hskey,
                on_message=self.on_message,
                on_close=self.on_close)
        ws.on_open = self.on_open
        try:
            ws.run_forever()
        except KeyboardInterrupt:
            ws.close()

    # This isn't optimal, but because of the way this websocket client code
    # works, we have to end every method here with a send.  The server
    # acknowledges every send that you do with something, and it tells you the
    # game state so you can pick up where you left off.  You might need to
    # remember things in your code, though, if you want to make correct
    # decisions.
    def on_message(self, ws, message):
        print
        print 'Message:', message
        print
        if 'available' in message:
            self.player = message['available'][self.available_player]
            ws.send({'player': self.player})
        elif 'game_over' in message:
            print 'Game over, closing socket'
            ws.close()
        elif 'newturn' in message or 'connected' in message:
            # TODO: these messages are ugly; clean up the protocol a bit
            if 'player_state' in message:
                self.player_state = message['player_state']
            if 'game_state' in message:
                self.game_state = message['game_state']
            if message['game_state']['current_player'] == self.player:
                try:
                    old_player_state = self.player_state
                except AttributeError:
                    old_player_state = None
                player_state = message.get('player_state', old_player_state)
                self.take_turn(ws, player_state, message['game_state'])
        elif 'action_finished' in message:
            self.take_turn(ws, message['player_state'], message['game_state'])
        elif 'card_bought' in message:
            self.take_turn(ws, message['player_state'], message['game_state'])
        elif 'user_action' in message:
            attack = message.get('attacking_player', None)
            self.handle_action(ws, message, attack)
        elif 'attack_response' in message:
            if message['attacking_player'] == self.player:
                # Sadly, it seems this convoluted approach is the only way to
                # get the message to go to the right socket on the server.
                print 'Forwarding attack response to server'
                ws.send(message)
        elif 'connected' in message:
            pass
        elif 'newturn' in message:
            if 'player_state' in message:
                self.player_state = message['player_state']
                print 'Got updated player state.  My hand is:'
                print self.player_state['hand']
        else:
            print "Didn't know how to handle the last message"

    def on_close(self, ws):
        print "### closed ###"

    def on_open(self, ws):
        print 'Connection opened'
        ws.send({'game': 2})

    def take_turn(self, ws, player_state, game_state):
        # We save these here for future use, because this code has to be event
        # driven.
        self.player_state = player_state
        self.game_state = game_state
        if (game_state['current_player_actions'] > 0 and
                game_state['current_player_state'] == 'ACTIONS'):
            self.play_action(ws, player_state, game_state)
        elif game_state['current_player_buys'] > 0:
            self.buy_card(ws, player_state, game_state)
        else:
            ws.send({'endturn': 'end turn'})

    def play_action(self, ws, player_state, game_state):
        hand = [get_card_from_name(c[0], c[1]) for c in player_state['hand']]
        actions = [c for c in hand if c._is_action]
        if actions:
            action = self.r.choice(actions)
            to_remove = [action.cardname, action._card_num]
            print 'playing action', action.cardname
            # I don't think these four lines are necessary anymore, but I need
            # to write some tests to be sure before I remove them.
            player_state['hand'].remove(to_remove)
            game_state['current_player_actions'] -= 1
            self.player_state = player_state
            self.game_state = game_state
            ws.send({'playaction': action._card_num})
        else:
            self.buy_card(ws, player_state, game_state)

    def buy_card(self, ws, player_state, game_state):
        # For this agent, let's do some really simple stuff.  Only buy cards
        # that are worth at least 2 (no Copper or Curse).  If you have 3 or 6,
        # always buy coins, if you have 8, always buy a Province.  Else pick
        # something good at random.
        if game_state['current_player_buys'] == 0:
            ws.send({'endturn': 'end turn'})
            return
        hand = [get_card_from_name(c[0], c[1]) for c in player_state['hand']]
        coins = game_state['current_player_coins']
        if coins < 2:
            ws.send({'endturn': 'end turn'})
            return
        elif coins == 3:
            to_buy = 'Silver'
        elif coins == 6:
            to_buy = 'Gold'
        elif coins == 8:
            to_buy = 'Province'
        else:
            available_cards = get_available_cards(game_state, coins)
            highest_cost = max(c[0].cost() for c in available_cards)
            if highest_cost == 0:
                ws.send({'endturn': 'end turn'})
                return
            highest_cost_cards = [c for c in available_cards
                    if c[0].cost() == highest_cost]
            to_buy = self.r.choice(highest_cost_cards)[1]
        # I don't think these two lines are necessary anymore, but I need to
        # write some tests to be sure before I remove them.
        game_state['current_player_buys'] -= 1
        self.game_state = game_state
        print 'buying', to_buy
        ws.send({'buycard': to_buy})

    def handle_action(self, ws, received_message, attacking_player):
        game_state = self.game_state
        hand = self.player_state['hand']
        cards_in_hand = [get_card_from_name(c[0], c[1])
                for c in self.player_state['hand']]
        message = {}
        # This is because attack actions need to know the player that is
        # responding, and because attack responses need to be forwarded by the
        # server.
        if attacking_player:
            message['responding_player'] = self.player
            message['attacking_player'] = attacking_player
            message['attack_response'] = 'pues!'
        action = received_message['user_action']
        if 'gain_card_' in action:
            max_cost = int(action.split('_')[-1])
            available_cards = get_available_cards(game_state, max_cost)
            highest_cost = max(c[0].cost() for c in available_cards)
            highest_cost_cards = [c for c in available_cards
                    if c[0].cost() == highest_cost]
            gained = self.r.choice(highest_cost_cards)[1]
            message['gained'] = gained
            ws.send(message)
        elif 'gain_treasure_' in action:
            max_cost = int(action.split('_')[-1])
            # TODO: we need some checking in here, to make sure these cards are
            # available
            if max_cost == 3:
                gained = 'Silver'
            if max_cost == 6:
                gained = 'Gold'
            if max_cost == 9:
                #gained = 'Platinum'
                gained = 'Gold'
            message['gained'] = gained
            ws.send(message)
        elif action == 'trash_one':
            trashed = self.r.choice(hand)
            self.player_state['hand'].remove(trashed)
            message['trashed'] = trashed[1]
            ws.send(message)
        elif action == 'trash_any':
            message['trashed'] = []
            ws.send(message)
        elif action == 'trash_treasure':
            treasure = [c for c in cards_in_hand if c._is_treasure]
            if not treasure:
                message['trashed'] = -1
            else:
                trashed = self.r.choice(treasure)
                to_remove = [trashed.cardname, trashed._card_num]
                self.player_state['hand'].remove(to_remove)
                message['trashed'] = trashed._card_num
            ws.send(message)
        elif action == 'pick_action':
            actions = [c for c in cards_in_hand if c._is_action]
            message['gained'] = self.r.choice(actions).card_num
            ws.send(message)
        elif action == 'library_keep_card':
            message['keep'] = 'yes'
            ws.send(message)
        elif action == 'discard_any':
            message['discarded'] = []
            ws.send(message)
        elif action == 'discard_two':
            discarded = self.hand[:2]
            for d in discarded:
                self.player_state['hand'].remove(d)
            message['discarded'] = [d[1] for d in discarded]
            ws.send(message)
        elif action == 'discard_to_three':
            print 'Hand is currently:'
            print self.player_state['hand']
            discarded = self.player_state['hand'][3:]
            for d in discarded:
                self.player_state['hand'].remove(d)
            message['discarded'] = [d[1] for d in discarded]
            print 'After discard, hand is:'
            print self.player_state['hand']
            print 'sending message:', message
            ws.send(message)
        elif action == 'chancellor':
            message['reshuffle'] = 'yes'
            ws.send(message)
        elif action == 'gain_curse':
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
        elif action == 'bureaucrat_attacking':
            victory_cards = [c for c in cards_in_hand if c._is_victory]
            if not victory_cards:
                message['victory_card'] = -1
            else:
                message['victory_card'] = victory_cards[0]._card_num
            ws.send(message)
        else:
            raise ValueError("I don't know how to respond to this action: %s"
                    % action)


if __name__ == "__main__":
    import sys
    player = 0
    a = Agent(player)
    a.connect("ws://localhost:9000/socket.io/1/")


# vim: et sw=4 sts=4
