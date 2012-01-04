#!/usr/bin/env python

PORT = 9000

import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
import sys
sys.path.append(os.getcwd()+'/..')

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

from socketio import SocketIOServer
from dominion.game.models import Game

if __name__ == '__main__':
    for game in Game.objects.all():
        # This is suboptimal, but I don't know how else to reset connectedness
        # when the server is killed.  So until I figure out a better way, you
        # can only have one server running per database.  I suppose that's not
        # too unreasonable a limitation, is it?
        print "Resetting player connections for game", game.name
        for player in game.player_set.all():
            player.connected = False
            player.save()
    print 'Listening on port %s and on port 843 (flash policy server)' % PORT
    SocketIOServer(('', PORT), application,
            resource="socket.io").serve_forever()
