from django.http import HttpResponse

import sys
import traceback
from django.core.signals import got_request_exception
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
        else:
            print "ERROR: Message wasn't a list of 1 item: ", message
        if 'game' in message:
            game_id = message['game']
            available = get_available_players(game_id)
            socketio.send({'available': available})
        elif 'player' in message:
            player = message['player']
            connect_player(game_id, player)
            state = get_game_state(game_id)
            socketio.send({'state': state})
        elif 'endturn' in message:
            end_turn(game_id)
            state = get_game_state(game_id)
            socketio.broadcast({'state': state})
            socketio.send({'state': state})
        elif 'val' in message:
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

    return HttpResponse()


# GAME LOGIC METHODS
####################

# To be moved when I decide on an appropriate place for them

# We need to re-query for the game object in every method so that all of its
# fields are up to date; otherwise we would only have stale information in
# game.  This assumes that these messages are reasonably far apart, so that we
# don't get race conditions.  But that should be fine for the applications I'm
# considering.


def get_available_players(game_id):
    game = Game.objects.get(pk=game_id)
    connected_players = [p.player_num for p in
            game.player_set.filter(connected=True)]
    return [x+1 for x in range(game.num_players)]


def get_game_state(game_id):
    game = Game.objects.get(pk=game_id)
    return game.current_player


def end_turn(game_id):
    game = Game.objects.get(pk=game_id)
    current_player = game.current_player
    game.current_player = current_player % game.num_players + 1
    game.save()


def connect_player(game_id, player_num):
    game = Game.objects.get(pk=game_id)
    player = game.player_set.get(player_num=player_num)
    player.connected = True
    player.save()


def disconnect_player(game_id, player_num):
    game = Game.objects.get(pk=game_id)
    player = game.player_set.get(player_num=player_num)
    player.connected = False
    player.save()

# vim: et sw=4 sts=4
