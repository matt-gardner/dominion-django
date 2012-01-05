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


LOGGING = True

def log_info(*args):
    if LOGGING:
        string = ' '.join(str(x) for x in args)
        print string


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
            # We don't send anything here, because the action notifies when it
            # is finished.  Maybe we should change that to be more consistent,
            # but oh well.
        elif 'buycard' in message:
            cardname = message['buycard']
            buy_card(game_id, player, cardname)
            socketio.send({'card-bought': 'card bought'})
        elif 'endturn' in message:
            end_turn(game_id, player)
            game_state = get_game_state(game_id)
            # TODO: send player's new hand, too, so they can use it to know how
            # to respond to attacks.  This may obviate the need for the
            # "myturn" request.
            message = {'game-state': game_state, 'newturn': 'newturn'}
            socketio.broadcast(message)
            socketio.send(message)
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


def get_player(game_id, player_num):
    game = Game.objects.get(pk=game_id)
    return game.player_set.get(player_num=player_num)


def connect_player(game_id, player_num):
    player = get_player(game_id, player_num)
    player.connected = True
    player.save()
    log_info('Connected player', player_num, 'to game', game_id)


def disconnect_player(game_id, player_num):
    player = get_player(game_id, player_num)
    player.connected = False
    player.save()


def get_available_players(game_id):
    game = Game.objects.get(pk=game_id)
    connected_players = [p.player_num for p in
            game.player_set.filter(connected=True)]
    players = [x+1 for x in range(game.num_players)]
    available = [p for p in players if p not in connected_players]
    return available


def get_player_state(game_id, player_num):
    return PlayerState(game_id, player_num)


def get_game_state(game_id):
    return GameState(game_id)


def play_action(game_id, player_num, card_num, socket):
    player = get_player(game_id, player_num)
    player.play_action(card_num, socket)


def buy_card(game_id, player_num, cardname):
    player = get_player(game_id, player_num)
    player.buy_card(cardname)


def end_turn(game_id, player_num):
    game = Game.objects.get(pk=game_id)
    current_player = game.current_player
    if current_player != player_num:
        raise ValueError("Something's wrong...")
    game.current_player = current_player % game.num_players + 1
    game.save()
    player = game.player_set.get(player_num=player_num)
    player.end_turn()
    next_player = game.player_set.get(player_num=game.current_player)
    next_player.begin_turn()


# These objects are what we will be passing along the network to clients, so
# they are JSON-encodable dictionaries.  Do not try to save anything in here
# that is not JSON-encodable, or you will crash the socket communication.

class GameState(dict):
    def __init__(self, game_id):
        game = Game.objects.select_related().get(pk=game_id)
        self['current_player'] = game.current_player
        self['cardstacks'] = [(c.cardname, c.num_left) for c in
                game.cardset.cardstack_set.all()]


class PlayerState(dict):
    def __init__(self, game_id, player_num):
        player = get_player(game_id, player_num)
        hand = player.get_hand()
        self['hand'] = [(c.cardname, c._card_num) for c in hand]
        # These two pieces of information could be public in GameState instead
        # of just here in PlayerState, but we'll worry about that later.
        self['num-actions'] = player.num_actions
        self['num-buys'] = player.num_buys


# vim: et sw=4 sts=4
