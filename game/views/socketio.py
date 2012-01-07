from django.http import HttpResponse

import sys
import traceback
from datetime import datetime

from django.core.signals import got_request_exception

from dominion.game.logic import *
from dominion.game.models import Game

# This is so that exceptions are actually printed on the command line instead
# of just being swallowed up.  If you don't have these few lines, you can't
# really debug any of the socketio stuff.
def exception_printer(sender, **kwargs):
    print >> sys.stderr, ''.join(traceback.format_exception(*sys.exc_info()))

got_request_exception.connect(exception_printer)


# I think the strategy here should be that this just calls methods in game
# logic code depending on what messages it receives.  In the typical
# model-view-controller framework, this little piece of code is the controller.
def socketio(request):
    socketio = request.environ['socketio']
    if socketio.on_connect():
        socketio.broadcast({'announcement':
                socketio.session.session_id + ' connected'})

    game_id = None
    player = None
    while True:
        message = socketio.recv()

        if not socketio.connected():
            disconnect_player(game_id, player)
            socketio.broadcast({'announcement':
                    socketio.session.session_id + ' disconnected'})
            break
        if len(message) == 0:
            # Probably a heartbeat message - move along
            continue
        if len(message) == 1:
            message = message[0]
            print message
            start = datetime.now()
        else:
            print "ERROR: Message wasn't a list of 1 item: ", message
        if 'attack-response' in message:
            # I hope this works...
            socketio.broadcast(message)
        elif 'game' in message:
            game_id = message['game']
            available = get_available_players(game_id)
            socketio.send({'available': available})
        elif 'player' in message:
            player = message['player']
            connect_player(game_id, player)
            game_state = get_game_state(game_id)
            socketio.send({'connected': 'connected', 'game-state': game_state})
        elif 'myturn' in message:
            # TODO: this request may not be necessary anymore, because I'm
            # sending player_state on endturn
            if player == Game.objects.get(pk=game_id).current_player:
                player_state = get_player_state(game_id, player)
                game_state = get_game_state(game_id)
                message = {'yourturn': 'your turn',
                        'player-state': player_state,
                        'game-state': game_state}
                socketio.send(message)
            else:
                socketio.send({'notyourturn': 'not your turn'})
        elif 'playaction' in message:
            card_num = message['playaction']
            play_action(game_id, player, card_num, socketio)
            player_state = get_player_state(game_id, player)
            socketio.send({'action-finished': 'finished',
                    'player-state': player_state})
        elif 'buycard' in message:
            cardname = message['buycard']
            buy_card(game_id, player, cardname)
            player_state = get_player_state(game_id, player)
            socketio.send({'card-bought': 'card bought',
                    'player-state': player_state})
        elif 'endturn' in message:
            end_turn(game_id, player)
            game_state = get_game_state(game_id)
            # Tell everyone else that this turn is over
            message = {'game-state': game_state,
                    'newturn': 'newturn'}
            socketio.broadcast(message)
            # And tell the current player what his new hand is
            player_state = get_player_state(game_id, player)
            message['player-state'] = player_state
            socketio.send(message)
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
                socketio.broadcast(message)
                socketio.send(message)
            else:
                socketio.send({'announcement': "It's not your turn!"})
        else:
            print "ERROR: Got a message I didn't understand"
            print message
        end = datetime.now()
        delta = end - start
        seconds = delta.seconds + delta.microseconds / 1000000.0
        print 'processing took', seconds, 'seconds'
        print
        start = datetime.now()

    return HttpResponse()


# vim: et sw=4 sts=4
