#!/usr/bin/env python

from dominion.game.logic import *
from dominion.game.models import Game

from django_socketio.events import on_message

game_id = None
player = None

@on_message
def handle_message(request, socket, context, message):
    game_id = context.get('game_id', None)
    player = context.get('player', None)
    if 'attack_response' in message:
        # I hope this works...
        socket.broadcast(message)
    elif 'game' in message:
        context['game_id'] = message['game']
        game_id = context['game_id']
        available = get_available_players(game_id)
        socket.send({'available': available})
    elif 'player' in message:
        context['player'] = message['player']
        player = context['player']
        connect_player(game_id, player)
        game_state = get_game_state(game_id)
        player_state = get_player_state(game_id, player)
        socket.send({'connected': 'connected', 'game_state': game_state,
                'player_state': player_state})
    elif 'playaction' in message:
        card_num = message['playaction']
        play_action(game_id, player, card_num, socket)
        game_state = get_game_state(game_id)
        player_state = get_player_state(game_id, player)
        socket.send({'action_finished': 'finished',
                'player_state': player_state,
                'game_state': game_state})
    elif 'buycard' in message:
        cardname = message['buycard']
        buy_card(game_id, player, cardname)
        game_state = get_game_state(game_id)
        player_state = get_player_state(game_id, player)
        socket.send({'card_bought': 'card bought',
                'game_state': game_state,
                'player_state': player_state})
    elif 'endturn' in message:
        game_over = end_turn(game_id, player)
        if game_over:
            message = {'game_over': 'game over'}
            socket.broadcast(message)
            socket.send(message)
        else:
            game_state = get_game_state(game_id)
            # Tell everyone else that this turn is over
            message = {'game_state': game_state,
                    'newturn': 'newturn'}
            socket.broadcast(message)
            # And tell the current player what his new hand is
            player_state = get_player_state(game_id, player)
            player_message = dict()
            player_message.update(message)
            player_message['player_state'] = player_state
            socket.send(player_message)
    elif 'val' in message:
        # OLD CODE, from early testing.  Remove this when the web interface
        # is updated.
        game = Game.objects.get(pk=game_id)
        current_player = game.current_player
        if current_player == player:
            game.count += 1
            game.current_player = current_player % game.num_players + 1
            game.save()
            message = {'count': game.count,
                    'current_player': game.current_player}
            # We need to do both here, because broadcast only goes to other
            # people, not yourself.  I prefer just sending to everyone,
            # including yourself.
            socket.broadcast(message)
            socket.send(message)
        else:
            socket.send({'announcement': "It's not your turn!"})
    else:
        print "ERROR: Got a message I didn't understand"
        print message


# vim: et sw=4 sts=4
