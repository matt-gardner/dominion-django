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
        print message
        if 'game' in message:
            game = Game.objects.get(pk=message['game'])
            player = message['player']
            socketio.send({'count': game.count})
        elif 'val' in message:
            game.count += 1
            game.save()
            print game.count, game.pk
            message = {'count': game.count}
            socketio.broadcast(message)
        else:
            print "Got a message I didn't understand"

    return HttpResponse()
