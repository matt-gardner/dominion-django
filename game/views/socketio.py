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
    while True:
        message = socketio.recv()

        if not socketio.connected():
            socketio.broadcast({'announcement':
                    socketio.session.session_id + ' disconnected'})
            break
        if len(message) == 1 and type(message) == list:
            message = message[0]
        else:
            print "Message wasn't a list of 1 item...  Not sure what to do"
        if 'game' in message:
            game_id = message['game']
            player = message['player']
            game = Game.objects.get(pk=game_id)
            socketio.send({'count': game.count})
        elif 'val' in message:
            if not game_id:
                print 'Something bad happened... game_id is not initialized'
            # We need to re-query for the game object every time so that all of
            # its fields are up to date; otherwise we would only have stale
            # information in game.  This assumes that these messages are
            # reasonably far apart, so that we don't get race conditions.  But
            # that should be fine for the applications I'm considering.
            game = Game.objects.get(pk=game_id)
            game.count += 1
            game.save()
            print game.count, game.pk
            message = {'count': game.count}
            socketio.broadcast(message)
        else:
            print "Got a message I didn't understand"

    return HttpResponse()
