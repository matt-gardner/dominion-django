#!/usr/bin/env python

# NOTE: This is a modified version of django.db.transaction, to give better
# error messages.
import transaction
from dominion.game.models import Game


# TODO: this probably belongs in a more central location

LOGGING = True

def log_info(*args):
    if LOGGING:
        string = ' '.join(str(x) for x in args)
        print string


# GAME LOGIC METHODS
####################

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


@transaction.commit_manually
def play_action(game_id, player_num, card_num, socket):
    # It's possible that committing manually here could have some unintended
    # consequences, because some actions send messages to players, but I think
    # that things should still work fine.  I need some more testing to be sure,
    # though.
    player = get_player(game_id, player_num)
    player.play_action(card_num, socket)
    transaction.commit()


@transaction.commit_manually
def buy_card(game_id, player_num, cardname):
    player = get_player(game_id, player_num)
    player.buy_card(cardname)
    transaction.commit()


@transaction.commit_manually
def end_turn(game_id, player_num):
    game = Game.objects.get(pk=game_id)
    current_player = game.current_player
    if current_player != player_num:
        raise ValueError("Something's wrong...")
    game.current_player = current_player % game.num_players + 1
    game.save()
    player = game.player_set.get(player_num=player_num)
    player.end_turn()
    game.test_for_finished()
    if not game.finished:
        next_player = game.player_set.get(player_num=game.current_player)
        next_player.begin_turn()
    transaction.commit()
    return game.finished


# These objects are what we will be passing along the network to clients, so
# they are JSON-encodable dictionaries.  Do not try to save anything in here
# that is not JSON-encodable, or you will crash the socket communication.

class GameState(dict):
    def __init__(self, game_id):
        game = Game.objects.select_related().get(pk=game_id)
        self['current_player'] = game.current_player
        self['cardstacks'] = [(c.cardname, c.num_left) for c in
                game.cardset.cardstack_set.all()]
        if game.finished:
            self['game-over'] = 'game over!'


class PlayerState(dict):
    def __init__(self, game_id, player_num):
        player = get_player(game_id, player_num)
        hand = player.get_hand()
        self['hand'] = [(c.cardname, c._card_num) for c in hand]
        # These two pieces of information could be public in GameState instead
        # of just here in PlayerState, but we'll worry about that later.
        self['num-actions'] = player.num_actions
        self['num-buys'] = player.num_buys
        self['coins'] = player.coins

def main():
    pass


if __name__ == '__main__':
    main()

# vim: et sw=4 sts=4
