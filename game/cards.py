#!/usr/bin/env python


class Card(object):
    def __init__(self, card_num):
        self._card_num = card_num
        self._coins = 0
        self._cost = None
        self._victory_points = 0
        self._is_treasure = False
        self._is_action = False
        self._is_victory = False

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

    def starting_stack_size(self, num_players):
        return 10


# Coin cards
############

class TreasureCard(Card):
    def __init__(self):
        super(self, TreasureCard).__init__()
        self._is_treasure = True

class Copper(TreasureCard):
    def __init__(self):
        super(self, Copper).__init__()
        self._coins = 1
        self._cost = 0

    def starting_stack_size(self, num_players):
        return 60


class Silver(TreasureCard):
    def __init__(self):
        super(self, Silver).__init__()
        self._coins = 2
        self._cost = 3

    def starting_stack_size(self, num_players):
        return 40


class Gold(TreasureCard):
    def __init__(self):
        super(self, Gold).__init__()
        self._coins = 3
        self._cost = 6

    def starting_stack_size(self, num_players):
        return 30


# Victory cards
###############

class Curse(Card):
    def __init__(self):
        super(self, Curse).__init__()
        self._cost = 0
        self._victory_points = -1

    def starting_stack_size(self, num_players):
        return 30


class VictoryCard(Card):
    def __init__(self):
        super(self, VictoryCard).__init__()
        self.is_victory = True

    def starting_stack_size(self, num_players):
        if num_players == 2:
            return 8
        else:
            return 12


class Estate(VictoryCard):
    def __init__(self):
        super(self, Estate).__init__()
        self._cost = 2
        self._victory_points = 1


class Duchy(VictoryCard):
    def __init__(self):
        super(self, Duchy).__init__()
        self._cost = 5
        self._victory_points = 3


class Province(VictoryCard):
    def __init__(self):
        super(self, Province).__init__()
        self._cost = 8
        self._victory_points = 6


class Gardens(VictoryCard):
    def __init__(self):
        super(self, Gardens).__init__()
        self._cost = 4

    def victory_points(self, player):
        return int(player.deck.get_num_cards() / 10)


# Action cards
##############

class ActionCard(Card):
    def __init__(self):
        super(self, ActionCard).__init__()
        self._is_action = True


class Adventurer(ActionCard):
    def __init__(self):
        super(self, Adventurer).__init__()
        self._cost = 6

    def play_action(self, player, socket):
        num_treasure = 0
        deck = player.deck
        while num_treasure < 2:
            card = player.card_from_card_num(deck.draw_card_to_play())
            if card._is_treasure:
                num_treasure += 1
                deck.move_card_from_play_to_hand(card)
                player.coins += card.coins()


class Bureaucrat(ActionCard):
    def __init__(self):
        super(self, Bureaucrat).__init__()
        self._cost = 4

    def play_action(self, player, socket):
        silver_stack = player.game.cardset.cardstack_set.get(cardname='Silver')
        if silver_stack.num_left != 0:
            silver_stack.num_left -= 1
            silver_stack.save()
            player.deck.add_card_to_top_of_deck('Silver')
        # Attack other players
        raise NotImplementedError()


class Cellar(ActionCard):
    def __init__(self):
        super(self, Cellar).__init__()
        self._cost = 2

    def play_action(self, player, socket):
        player.num_actions += 1
        # Ask which cards to discard
        raise NotImplementedError()
        for i in range(num_discarded):
            player.draw_card()


class Chancellor(ActionCard):
    def __init__(self):
        super(self, Chancellor).__init__()
        self._cost = 3

    def play_action(self, player, socket):
        player.coins += 2
        # I don't remember what this action is...
        raise NotImplementedError()


class Chapel(ActionCard):
    def __init__(self):
        super(self, Chapel).__init__()
        self._cost = 2

    def play_action(self, player, socket):
        # Ask which cards to trash
        raise NotImplementedError()
        for card_num in cards_to_trash:
            player.trash_card(card_num)


class CouncilRoom(ActionCard):
    def __init__(self):
        super(self, CouncilRoom).__init__()
        self._cost = 5

    def play_action(self, player, socket):
        player.draw_card()
        player.draw_card()
        player.draw_card()
        player.draw_card()
        player.num_buys += 1
        for other in player.game.get_other_players():
            other.draw_card()


class Feast(ActionCard):
    def __init__(self):
        super(self, Feast).__init__()
        self._cost = 4

    def play_action(self, player, socket):
        # Pick which card to buy
        raise NotImplementedError()
        player.trash_card(self._card_num)


class Festival(ActionCard):
    def __init__(self):
        super(self, Festival).__init__()
        self._cost = 5

    def play_action(self, player, socket):
        player.num_actions += 2
        player.num_buys += 1
        player.coins += 2


class Laboratory(ActionCard):
    def __init__(self):
        super(self, Laboratory).__init__()
        self._cost = 5

    def play_action(self, player, socket):
        player.num_actions += 1
        player.draw_card()
        player.draw_card()


class Library(ActionCard):
    def __init__(self):
        super(self, Library).__init__()
        self._cost = 5

    def play_action(self, player, socket):
        deck = player.deck
        while len(deck.cards_in_hand.split()) < 7:
            card = player.card_from_card_num(deck.draw_card_to_play())
            if card._is_action:
                # Ask whether to keep card or not
                raise NotImplementedError()
                continue
            deck.move_card_from_play_to_hand(card)
            player.coins += card.coins()



class Market(ActionCard):
    def __init__(self):
        super(self, Market).__init__()
        self._cost = 5

    def play_action(self, player, socket):
        player.coins += 1
        player.num_actions += 1
        player.num_buys += 1
        player.draw_card()


class Militia(ActionCard):
    def __init__(self):
        super(self, Militia).__init__()
        self._cost = 4

    def play_action(self, player, socket):
        player.coins += 2
        # Attack other players
        raise NotImplementedError()


class Mine(ActionCard):
    def __init__(self):
        super(self, Mine).__init__()
        self._cost = 5

    def play_action(self, player, socket):
        # Choose card from hand to upgrade
        raise NotImplementedError()
        # Choose card to buy (or do it automatically...)
        raise NotImplementedError()


class Moat(ActionCard):
    def __init__(self):
        super(self, Moat).__init__()
        self._cost = 2

    def play_action(self, player, socket):
        player.draw_card()
        player.draw_card()


class MoneyLender(ActionCard):
    def __init__(self):
        super(self, MoneyLender).__init__()
        self._cost = 4

    def play_action(self, player, socket):
        # Choose copper card to trash
        raise NotImplementedError()
        if trashed:
            player.coins += 3


class Remodel(ActionCard):
    def __init__(self):
        super(self, Remodel).__init__()
        self._cost = 4

    def play_action(self, player, socket):
        # Pick card from hand to get rid of
        raise NotImplementedError()
        # Pick card to buy
        raise NotImplementedError()


class Smithy(ActionCard):
    def __init__(self):
        super(self, Smithy).__init__()
        self._cost = 4

    def play_action(self, player, socket):
        player.draw_card()
        player.draw_card()
        player.draw_card()


class Spy(ActionCard):
    def __init__(self):
        super(self, Spy).__init__()
        self._cost = 4

    def play_action(self, player, socket):
        self.draw_card()
        self.num_actions += 1
        # Attack other players, choose what to do
        raise NotImplementedError()


class Thief(ActionCard):
    def __init__(self):
        super(self, Thief).__init__()
        self._cost = 4

    def play_action(self, player, socket):
        for other in player.game.get_other_players():
            raise NotImplementedError()


class ThroneRoom(ActionCard):
    def __init__(self):
        super(self, ThroneRoom).__init__()
        self._cost = 4

    def play_action(self, player, socket):
        raise NotImplementedError()


class Village(ActionCard):
    def __init__(self):
        super(self, Village).__init__()
        self._cost = 3

    def play_action(self, player, socket):
        player.num_actions += 2
        player.draw_card()


class Witch(ActionCard):
    def __init__(self):
        super(self, Witch).__init__()
        self._cost = 5

    def play_action(self, player, socket):
        player.draw_card()
        player.draw_card()
        raise NotImplementedError()


class Woodcutter(ActionCard):
    def __init__(self):
        super(self, Woodcutter).__init__()
        self._cost = 3

    def play_action(self, player, socket):
        player.num_buys += 1
        player.coins += 2


class Workshop(ActionCard):
    def __init__(self):
        super(self, Workshop).__init__()
        self._cost = 3

    def play_action(self, player, socket):
        raise NotImplementedError()


# vim: et sw=4 sts=4
