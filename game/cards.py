#!/usr/bin/env python

from dominion.game.socketio_base import get_message

actions = {}
actions['chancellor'] = 'Do you want to reshuffle your deck?'
actions['discard-any'] = 'Pick any number of cards from your hand to discard'
actions['discard-to-three'] = 'Discard cards from your hand down to three cards'
actions['discard-two'] = 'Discard two cards from your hand'
actions['gain-card-0'] = 'Gain a card costing up to 1 coins'
actions['gain-card-1'] = 'Gain a card costing up to 1 coins'
actions['gain-card-2'] = 'Gain a card costing up to 2 coins'
actions['gain-card-3'] = 'Gain a card costing up to 3 coins'
actions['gain-card-4'] = 'Gain a card costing up to 4 coins'
actions['gain-card-5'] = 'Gain a card costing up to 5 coins'
actions['gain-card-6'] = 'Gain a card costing up to 6 coins'
actions['gain-card-7'] = 'Gain a card costing up to 7 coins'
actions['gain-card-8'] = 'Gain a card costing up to 8 coins'
actions['library-keep-card'] = 'Keep this action card or discard it?'
actions['pick-action'] = 'Pick an action card from your hand'
actions['trash-any'] = 'Pick any number of cards from your hand to trash'
actions['trash-one'] = 'Pick a card from your hand to trash'
actions['trash-treasure'] = 'Pick a treasure card to trash'

class Card(object):
    def __init__(self, card_num):
        self._card_num = card_num
        self._coins = 0
        self._cost = None
        self._victory_points = 0
        self._is_treasure = False
        self._is_action = False
        self._is_victory = False
        self.cardname = None

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
    def __init__(self, card_num):
        super(TreasureCard, self).__init__(card_num)
        self._is_treasure = True
        self.cardname = None


class Copper(TreasureCard):
    def __init__(self, card_num):
        super(Copper, self).__init__(card_num)
        self._coins = 1
        self._cost = 0
        self.cardname = 'Copper'

    def starting_stack_size(self, num_players):
        return 60


class Silver(TreasureCard):
    def __init__(self, card_num):
        super(Silver, self).__init__(card_num)
        self._coins = 2
        self._cost = 3
        self.cardname = 'Silver'

    def starting_stack_size(self, num_players):
        return 40


class Gold(TreasureCard):
    def __init__(self, card_num):
        super(Gold, self).__init__(card_num)
        self._coins = 3
        self._cost = 6
        self.cardname = 'Gold'

    def starting_stack_size(self, num_players):
        return 30


# Victory cards
###############

class Curse(Card):
    def __init__(self, card_num):
        super(Curse, self).__init__(card_num)
        self._cost = 0
        self._victory_points = -1
        self.cardname = 'Curse'

    def starting_stack_size(self, num_players):
        return 30


class VictoryCard(Card):
    def __init__(self, card_num):
        super(VictoryCard, self).__init__(card_num)
        self.is_victory = True

    def starting_stack_size(self, num_players):
        if num_players == 2:
            return 8
        else:
            return 12


class Estate(VictoryCard):
    def __init__(self, card_num):
        super(Estate, self).__init__(card_num)
        self._cost = 2
        self._victory_points = 1
        self.cardname = 'Estate'


class Duchy(VictoryCard):
    def __init__(self, card_num):
        super(Duchy, self).__init__(card_num)
        self._cost = 5
        self._victory_points = 3
        self.cardname = 'Duchy'


class Province(VictoryCard):
    def __init__(self, card_num):
        super(Province, self).__init__(card_num)
        self._cost = 8
        self._victory_points = 6
        self.cardname = 'Province'


class Gardens(VictoryCard):
    def __init__(self, card_num):
        super(Gardens, self).__init__(card_num)
        self._cost = 4
        self.cardname = 'Gardens'

    def victory_points(self, player):
        return int(player.deck.get_num_cards() / 10)


# Action cards
##############

class ActionCard(Card):
    def __init__(self, card_num):
        super(ActionCard, self).__init__(card_num)
        self._is_action = True


class Adventurer(ActionCard):
    def __init__(self, card_num):
        super(Adventurer, self).__init__(card_num)
        self._cost = 6
        self.cardname = 'Adventurer'

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
    def __init__(self, card_num):
        super(Bureaucrat, self).__init__(card_num)
        self._cost = 4
        self.cardname = 'Bureaucrat'

    def play_action(self, player, socket):
        silver_stack = player.game.cardset.cardstack_set.get(cardname='Silver')
        if silver_stack.num_left != 0:
            silver_stack.num_left -= 1
            silver_stack.save()
            player.deck.add_card_to_top_of_deck('Silver')
        # Attack other players
        raise NotImplementedError()


class Cellar(ActionCard):
    def __init__(self, card_num):
        super(Cellar, self).__init__(card_num)
        self._cost = 2
        self.cardname = 'Cellar'

    def play_action(self, player, socket):
        player.num_actions += 1
        # Ask which cards to discard
        socket.send({'user-action': 'discard-any'})
        message = get_message(socket)
        for num in message['discarded']:
            player.discard_card(num)
            player.draw_card()


class Chancellor(ActionCard):
    def __init__(self, card_num):
        super(Chancellor, self).__init__(card_num)
        self._cost = 3
        self.cardname = 'Chancellor'

    def play_action(self, player, socket):
        player.coins += 2
        socket.send({'user-action': 'chancellor'})
        message = get_message(socket)
        if message['reshuffle'] == 'yes':
            deck = player.deck.cards_in_deck.split()
            discard = player.deck.cards_in_discard.split()
            discard.extend(deck)
            player.deck.cards_in_deck = ''
            player.deck.cards_in_discard = ' '.join(discard)
            player.deck.save()


class Chapel(ActionCard):
    def __init__(self, card_num):
        super(Chapel, self).__init__(card_num)
        self._cost = 2
        self.cardname = 'Chapel'

    def play_action(self, player, socket):
        # Ask which cards to trash
        socket.send({'user-action': 'trash-any'})
        message = get_message(socket)
        for num in message['trashed']:
            player.trash_card(num)


class CouncilRoom(ActionCard):
    def __init__(self, card_num):
        super(CouncilRoom, self).__init__(card_num)
        self._cost = 5
        self.cardname = 'CouncilRoom'

    def play_action(self, player, socket):
        player.draw_card()
        player.draw_card()
        player.draw_card()
        player.draw_card()
        player.num_buys += 1
        for other in player.game.get_other_players():
            other.draw_card()


class Feast(ActionCard):
    def __init__(self, card_num):
        super(Feast, self).__init__(card_num)
        self._cost = 4
        self.cardname = 'Feast'

    def play_action(self, player, socket):
        # Pick which card to buy
        socket.send({'user-action': 'gain-card-5'})
        message = get_message(socket)
        player.gain_card(message['gained'])
        player.trash_card(self._card_num)


class Festival(ActionCard):
    def __init__(self, card_num):
        super(Festival, self).__init__(card_num)
        self._cost = 5
        self.cardname = 'Festival'

    def play_action(self, player, socket):
        player.num_actions += 2
        player.num_buys += 1
        player.coins += 2


class Laboratory(ActionCard):
    def __init__(self, card_num):
        super(Laboratory, self).__init__(card_num)
        self._cost = 5
        self.cardname = 'Laboratory'

    def play_action(self, player, socket):
        player.num_actions += 1
        player.draw_card()
        player.draw_card()


class Library(ActionCard):
    def __init__(self, card_num):
        super(Library, self).__init__(card_num)
        self._cost = 5
        self.cardname = 'Library'

    def play_action(self, player, socket):
        deck = player.deck
        while len(deck.cards_in_hand.split()) < 7:
            card = player.card_from_card_num(deck.draw_card_to_play())
            if card._is_action:
                # Ask whether to keep card or not
                socket.send({'user-action': 'library-keep-card'})
                message = get_message(socket)
                if message['keep'] == 'yes':
                    continue
            deck.move_card_from_play_to_hand(card._card_num)
            player.coins += card.coins()



class Market(ActionCard):
    def __init__(self, card_num):
        super(Market, self).__init__(card_num)
        self._cost = 5
        self.cardname = 'Market'

    def play_action(self, player, socket):
        player.coins += 1
        player.num_actions += 1
        player.num_buys += 1
        player.draw_card()


class Militia(ActionCard):
    def __init__(self, card_num):
        super(Militia, self).__init__(card_num)
        self._cost = 4
        self.cardname = 'Militia'

    def play_action(self, player, socket):
        player.coins += 2
        # Attack other players
        raise NotImplementedError()


class Mine(ActionCard):
    def __init__(self, card_num):
        super(Mine, self).__init__(card_num)
        self._cost = 5
        self.cardname = 'Mine'

    def play_action(self, player, socket):
        # Choose card from hand to upgrade
        socket.send({'user-action': 'trash-treasure'})
        message = get_message(socket)
        player.trash_card(message['trashed'])
        # Choose card to buy (or do it automatically...)
        socket.send({'user-action': 'gain-treasure'})
        message = get_message(socket)
        player.gain_card(message['gained'])


class Moat(ActionCard):
    def __init__(self, card_num):
        super(Moat, self).__init__(card_num)
        self._cost = 2
        self.cardname = 'Moat'

    def play_action(self, player, socket):
        player.draw_card()
        player.draw_card()


class MoneyLender(ActionCard):
    def __init__(self, card_num):
        super(MoneyLender, self).__init__(card_num)
        self._cost = 4
        self.cardname = 'MoneyLender'

    def play_action(self, player, socket):
        # Choose copper card to trash
        socket.send({'user-action': 'trash-copper'})
        message = get_message(socket)
        if message['trashed'] != 'None':
            player.trash_card(message['trashed'])
            player.coins += 3


class Remodel(ActionCard):
    def __init__(self, card_num):
        super(Remodel, self).__init__(card_num)
        self._cost = 4
        self.cardname = 'Remodel'

    def play_action(self, player, socket):
        # Pick card from hand to get rid of
        socket.send({'user-action': 'trash-one'})
        message = get_message(socket)
        card = player.card_from_card_num(message['trashed'])
        player.trash_card(message['trashed'])
        coins = card.coins() + 2
        # Pick card to buy
        socket.send({'user-action': 'gain-card-%d' % coins})
        message = get_message(socket)
        player.gain_card(message['gained'])


class Smithy(ActionCard):
    def __init__(self, card_num):
        super(Smithy, self).__init__(card_num)
        self._cost = 4
        self.cardname = 'Smithy'

    def play_action(self, player, socket):
        player.draw_card()
        player.draw_card()
        player.draw_card()


class Spy(ActionCard):
    def __init__(self, card_num):
        super(Spy, self).__init__(card_num)
        self._cost = 4
        self.cardname = 'Spy'

    def play_action(self, player, socket):
        self.draw_card()
        self.num_actions += 1
        # Attack other players, choose what to do
        raise NotImplementedError()


class Thief(ActionCard):
    def __init__(self, card_num):
        super(Thief, self).__init__(card_num)
        self._cost = 4
        self.cardname = 'Thief'

    def play_action(self, player, socket):
        for other in player.game.get_other_players():
            raise NotImplementedError()


class ThroneRoom(ActionCard):
    def __init__(self, card_num):
        super(ThroneRoom, self).__init__(card_num)
        self._cost = 4
        self.cardname = 'ThroneRoom'

    def play_action(self, player, socket):
        socket.send({'user-action': 'pick-action'})
        message = get_message(socket)
        card = player.card_from_card_num(message['picked'])
        card.play_action(player, socket)
        card.play_action(player, socket)


class Village(ActionCard):
    def __init__(self, card_num):
        super(Village, self).__init__(card_num)
        self._cost = 3
        self.cardname = 'Village'

    def play_action(self, player, socket):
        player.num_actions += 2
        player.draw_card()


class Witch(ActionCard):
    def __init__(self, card_num):
        super(Witch, self).__init__(card_num)
        self._cost = 5
        self.cardname = 'Witch'

    def play_action(self, player, socket):
        player.draw_card()
        player.draw_card()
        raise NotImplementedError()


class Woodcutter(ActionCard):
    def __init__(self, card_num):
        super(Woodcutter, self).__init__(card_num)
        self._cost = 3
        self.cardname = 'Woodcutter'

    def play_action(self, player, socket):
        player.num_buys += 1
        player.coins += 2


class Workshop(ActionCard):
    def __init__(self, card_num):
        super(Workshop, self).__init__(card_num)
        self._cost = 3
        self.cardname = 'Workshop'

    def play_action(self, player, socket):
        # Pick which card to buy
        socket.send({'user-action': 'gain-card-4'})
        message = get_message(socket)
        player.gain_card(message['gained'])


card_from_name = {
        'Copper': Copper,
        'Silver': Silver,
        'Gold': Gold,
        'Curse': Curse,
        'Estate': Estate,
        'Duchy': Duchy,
        'Province': Province,
        'Gardens': Gardens,
        'Adventurer': Adventurer,
        'Bureaucrat': Bureaucrat,
        'Cellar': Cellar,
        'Chancellor': Chancellor,
        'Chapel': Chapel,
        'CouncilRoom': CouncilRoom,
        'Feast': Feast,
        'Festival': Festival,
        'Laboratory': Laboratory,
        'Library': Library,
        'Market': Market,
        'Militia': Militia,
        'Mine': Mine,
        'Moat': Moat,
        'MoneyLender': MoneyLender,
        'Remodel': Remodel,
        'Smithy': Smithy,
        'Spy': Spy,
        'Thief': Thief,
        'ThroneRoom': ThroneRoom,
        'Village': Village,
        'Witch': Witch,
        'Woodcutter': Woodcutter,
        'Workshop': Workshop,
        }

# vim: et sw=4 sts=4
