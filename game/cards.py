#!/usr/bin/env python


class Card(object):
    def __init__(self):
        self._coins = 0
        self._cost = None
        self._victory_points = 0

    def play_action(self, player, socket):
        raise IllegalActionError("This card has no action")

    def coins(self):
        return self._coins

    def cost(self):
        if self._cost == None:
            raise ValueError("Card class forgot to specify cost")
        return self._cost

    def victory_points(self, player):
        return self._victory_points


# Coin cards
############

class Copper(Card):
    def __init__(self):
        super(self, Copper).__init__()
        self._coins = 1
        self._cost = 0


class Silver(Card):
    def __init__(self):
        super(self, Silver).__init__()
        self._coins = 2
        self._cost = 3


class Gold(Card):
    def __init__(self):
        super(self, Gold).__init__()
        self._coins = 3
        self._cost = 6


# Victory cards
###############

class Estate(Card):
    def __init__(self):
        super(self, Estate).__init__()
        self._cost = 2
        self._victory_points = 1


class Duchy(Card):
    def __init__(self):
        super(self, Duchy).__init__()
        self._cost = 5
        self._victory_points = 3


class Province(Card):
    def __init__(self):
        super(self, Province).__init__()
        self._cost = 8
        self._victory_points = 6


class Curse(Card):
    def __init__(self):
        super(self, Curse).__init__()
        self._cost = 0
        self._victory_points = -1


class Gardens(Card):
    def __init__(self):
        super(self, Gardens).__init__()
        self._cost = 4

    def victory_points(self, player):
        return int(player.deck.get_num_cards() / 10)


# Action cards
##############

class Adventurer(Card):
    def __init__(self):
        super(self, Adventurer).__init__()
        self._cost = 6

    def play_action(self, player, socket):
        raise NotImplementedError()


class Bureaucrat(Card):
    def __init__(self):
        super(self, Bureaucrat).__init__()
        self._cost = 4

    def play_action(self, player, socket):
        raise NotImplementedError()


class Cellar(Card):
    def __init__(self):
        super(self, Cellar).__init__()
        self._cost = 2

    def play_action(self, player, socket):
        player.num_actions += 1
        raise NotImplementedError()


class Chancellor(Card):
    def __init__(self):
        super(self, Chancellor).__init__()
        self._cost = 3

    def play_action(self, player, socket):
        player.coins += 2
        raise NotImplementedError()


class Chapel(Card):
    def __init__(self):
        super(self, Chapel).__init__()
        self._cost = 2

    def play_action(self, player, socket):
        raise NotImplementedError()


class CouncilRoom(Card):
    def __init__(self):
        super(self, CouncilRoom).__init__()
        self._cost = 5

    def play_action(self, player, socket):
        player.draw_card()
        player.draw_card()
        player.draw_card()
        player.draw_card()
        player.num_buys += 1
        raise NotImplementedError()


class Feast(Card):
    def __init__(self):
        super(self, Feast).__init__()
        self._cost = 4

    def play_action(self, player, socket):
        raise NotImplementedError()


class Festival(Card):
    def __init__(self):
        super(self, Festival).__init__()
        self._cost = 5

    def play_action(self, player, socket):
        player.num_actions += 2
        player.num_buys += 1
        player.coins += 2


class Laboratory(Card):
    def __init__(self):
        super(self, Laboratory).__init__()
        self._cost = 5

    def play_action(self, player, socket):
        player.num_actions += 1
        player.draw_card()
        player.draw_card()


class Library(Card):
    def __init__(self):
        super(self, Library).__init__()
        self._cost = 5

    def play_action(self, player, socket):
        raise NotImplementedError()


class Market(Card):
    def __init__(self):
        super(self, Market).__init__()
        self._cost = 5

    def play_action(self, player, socket):
        player.coins += 1
        player.num_actions += 1
        player.num_buys += 1
        player.draw_card()


class Militia(Card):
    def __init__(self):
        super(self, Militia).__init__()
        self._cost = 4

    def play_action(self, player, socket):
        player.coins += 2
        raise NotImplementedError()


class Mine(Card):
    def __init__(self):
        super(self, Mine).__init__()
        self._cost = 5

    def play_action(self, player, socket):
        raise NotImplementedError()


class Moat(Card):
    def __init__(self):
        super(self, Moat).__init__()
        self._cost = 2

    def play_action(self, player, socket):
        player.draw_card()
        player.draw_card()


class MoneyLender(Card):
    def __init__(self):
        super(self, MoneyLender).__init__()
        self._cost = 4

    def play_action(self, player, socket):
        raise NotImplementedError()


class Remodel(Card):
    def __init__(self):
        super(self, Remodel).__init__()
        self._cost = 4

    def play_action(self, player, socket):
        raise NotImplementedError()


class Smithy(Card):
    def __init__(self):
        super(self, Smithy).__init__()
        self._cost = 4

    def play_action(self, player, socket):
        player.draw_card()
        player.draw_card()
        player.draw_card()


class Spy(Card):
    def __init__(self):
        super(self, Spy).__init__()
        self._cost = 4

    def play_action(self, player, socket):
        self.draw_card()
        self.num_actions += 1
        raise NotImplementedError()


class Thief(Card):
    def __init__(self):
        super(self, Thief).__init__()
        self._cost = 4

    def play_action(self, player, socket):
        raise NotImplementedError()


class ThroneRoom(Card):
    def __init__(self):
        super(self, ThroneRoom).__init__()
        self._cost = 4

    def play_action(self, player, socket):
        raise NotImplementedError()


class Village(Card):
    def __init__(self):
        super(self, Village).__init__()
        self._cost = 3

    def play_action(self, player, socket):
        player.num_actions += 2
        player.draw_card()


class Witch(Card):
    def __init__(self):
        super(self, Witch).__init__()
        self._cost = 5

    def play_action(self, player, socket):
        player.draw_card()
        player.draw_card()
        raise NotImplementedError()


class Woodcutter(Card):
    def __init__(self):
        super(self, Woodcutter).__init__()
        self._cost = 3

    def play_action(self, player, socket):
        player.num_buys += 1
        player.coins += 2


class Workshop(Card):
    def __init__(self):
        super(self, Workshop).__init__()
        self._cost = 3

    def play_action(self, player, socket):
        raise NotImplementedError()


# vim: et sw=4 sts=4
