from django.http import HttpResponse

import sys
import traceback
from django.core.signals import got_request_exception
from dominion.game.models import Game

def exception_printer(sender, **kwargs):
    print >> sys.stderr, ''.join(traceback.format_exception(*sys.exc_info()))

got_request_exception.connect(exception_printer)

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
            socketio.broadcast({'announcement':
                    socketio.session.session_id + ' disconnected'})
            break
        if len(message) == 1 and type(message) == list:
            message = message[0]
        else:
            print "ERROR: Message wasn't a list of 1 item"
        if 'game' in message:
            game_id = message['game']
            game = Game.objects.get(pk=game_id)
            connected_players = [p.player_num for p in
                    game.player_set.filter(connected=True)]
            available = [x+1 for x in range(game.num_players)]
            socketio.send({'available': available})
        elif 'player' in message:
            game = Game.objects.get(pk=game_id)
            player = message['player']
            socketio.send({'count': game.count})
        elif 'val' in message:
            if not game_id:
                print 'ERROR: game_id is not initialized'
            if not player:
                print 'ERROR: player is not initialized'
            # We need to re-query for the game object every time so that all of
            # its fields are up to date; otherwise we would only have stale
            # information in game.  This assumes that these messages are
            # reasonably far apart, so that we don't get race conditions.  But
            # that should be fine for the applications I'm considering.
            game = Game.objects.get(pk=game_id)
            current_player = game.current_player
            if current_player == player:
                game.count += 1
                game.current_player = current_player % game.num_players + 1
                game.save()
                message = {'count': game.count}
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
