#!/usr/bin/env python

from dominion.game.socketio_base import get_message

actions = {}
actions['chancellor'] = 'Do you want to reshuffle your deck?'
actions['discard_any'] = 'Pick any number of cards from your hand to discard'
actions['discard_to_three'] = 'Discard cards from your hand down to three cards'
actions['discard_two'] = 'Discard two cards from your hand'
actions['gain_card_0'] = 'Gain a card costing up to 1 coins'
actions['gain_card_1'] = 'Gain a card costing up to 1 coins'
actions['gain_card_2'] = 'Gain a card costing up to 2 coins'
actions['gain_card_3'] = 'Gain a card costing up to 3 coins'
actions['gain_card_4'] = 'Gain a card costing up to 4 coins'
actions['gain_card_5'] = 'Gain a card costing up to 5 coins'
actions['gain_card_6'] = 'Gain a card costing up to 6 coins'
actions['gain_card_7'] = 'Gain a card costing up to 7 coins'
actions['gain_card_8'] = 'Gain a card costing up to 8 coins'
actions['library_keep_card'] = 'Keep this action card or discard it?'
actions['pick_action'] = 'Pick an action card from your hand'
actions['trash_any'] = 'Pick any number of cards from your hand to trash'
actions['trash_one'] = 'Pick a card from your hand to trash'
actions['trash_treasure'] = 'Pick a treasure card to trash'

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

    def starting_stack_size(self, num_players):
        return 24


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
        game = player.game
        response_needed = set()
        for other in game.get_other_players():
            response_needed.add(other.player_num)
        socket.broadcast({'user_action': 'bureaucrat',
                'attacking_player': player.player_num})
        while response_needed:
            message = get_message(socket)
            player_num = message['responding_player']
            other = player.game.player_set.get(player_num=player_num)
            if 'moat' not in message:
                victory_card = message['victory_card']
                if victory_card != -1:
                    # We don't currently validate that this is indeed a victory
                    # card.
                    other.deck.card_from_hand_to_top_of_deck(victory_card)
            response_needed.remove(message['responding_player'])


class Cellar(ActionCard):
    def __init__(self, card_num):
        super(Cellar, self).__init__(card_num)
        self._cost = 2
        self.cardname = 'Cellar'

    def play_action(self, player, socket):
        player.num_actions += 1
        # Ask which cards to discard
        socket.send({'user_action': 'discard_any'})
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
        socket.send({'user_action': 'chancellor'})
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
        socket.send({'user_action': 'trash_any'})
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
        socket.send({'user_action': 'gain_card_5'})
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
                socket.send({'user_action': 'library_keep_card'})
                message = get_message(socket)
                if message.get('keep', 'no') != 'yes':
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
        response_needed = set()
        for other in player.game.get_other_players():
            response_needed.add(other.player_num)
        socket.broadcast({'user_action': 'discard_to_three',
                'attacking_player': player.player_num})
        while response_needed:
            message = get_message(socket)
            player_num = message['responding_player']
            other = player.game.player_set.get(player_num=player_num)
            if 'moat' not in message:
                for card_num in message['discarded']:
                    other.discard_card(card_num)
            response_needed.remove(message['responding_player'])


class Mine(ActionCard):
    def __init__(self, card_num):
        super(Mine, self).__init__(card_num)
        self._cost = 5
        self.cardname = 'Mine'

    def play_action(self, player, socket):
        # Choose card from hand to upgrade
        socket.send({'user_action': 'trash_treasure'})
        message = get_message(socket)
        if message['trashed'] == -1:
            return
        card = player.card_from_card_num(message['trashed'])
        player.trash_card(message['trashed'])
        # Choose card to buy (or do it automatically...)
        # TODO: the message here should make it clear that the card is going to
        # the hand, as that could affect decision making
        socket.send({'user_action': 'gain_treasure_%d' % (card.cost() + 3)})
        message = get_message(socket)
        player.gain_card_to_hand(message['gained'])


class Moat(ActionCard):
    def __init__(self, card_num):
        super(Moat, self).__init__(card_num)
        self._cost = 2
        self.cardname = 'Moat'

    def play_action(self, player, socket):
        player.draw_card()
        player.draw_card()


class Moneylender(ActionCard):
    def __init__(self, card_num):
        super(Moneylender, self).__init__(card_num)
        self._cost = 4
        self.cardname = 'Moneylender'

    def play_action(self, player, socket):
        # Choose copper card to trash
        socket.send({'user_action': 'trash_copper'})
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
        socket.send({'user_action': 'trash_one'})
        message = get_message(socket)
        card = player.card_from_card_num(message['trashed'])
        player.trash_card(message['trashed'])
        coins = card.coins() + 2
        # Pick card to buy
        socket.send({'user_action': 'gain_card_%d' % coins})
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
        player.draw_card()
        player.num_actions += 1
        # Attack other players, choose what to do
        response_needed = set()
        for other in player.game.get_other_players():
            response_needed.add(other.player_num)
        socket.broadcast({'user_action': 'spy',
                'attacking_player': player.player_num})
        to_spy_on = set([player])
        while response_needed:
            message = get_message(socket)
            player_num = message['responding_player']
            other = player.game.player_set.get(player_num=player_num)
            if 'ok' in message:
                to_spy_on.add(other)
            elif 'moat' in message:
                pass
            response_needed.remove(message['responding_player'])
        for p in to_spy_on:
            card = p.deck.top_card()
            if card == -1:
                continue
            socket.send({'user_action': 'spying', 'player': p.player_num,
                    'cardname': p.card_from_card_num(card).cardname})
            message = get_message(socket)
            if 'discard' in message:
                discard = p.deck.cards_in_discard.split()
                deck = p.deck.cards_in_deck.split()
                discard.append(deck[0])
                deck = deck[1:]
                p.deck.cards_in_discard = ' '.join(discard)
                p.deck.cards_in_deck = ' '.join(deck)
                p.deck.save()


class Thief(ActionCard):
    def __init__(self, card_num):
        super(Thief, self).__init__(card_num)
        self._cost = 4
        self.cardname = 'Thief'

    def play_action(self, player, socket):
        response_needed = set()
        for other in player.game.get_other_players():
            response_needed.add(other.player_num)
        socket.broadcast({'user_action': 'thief',
                'attacking_player': player.player_num})
        to_steal_from = set()
        while response_needed:
            message = get_message(socket)
            player_num = message['responding_player']
            other = player.game.player_set.get(player_num=player_num)
            if 'ok' in message:
                to_steal_from.add(other)
            elif 'moat' in message:
                pass
            response_needed.remove(message['responding_player'])
        for p in to_steal_from:
            # TODO: Not really safe yet if player has 0 or 1 cards in deck
            cards = [p.card_from_card_num(c)
                    for c in p.deck.cards_in_deck.split()[0:2]]
            p.deck.cards_in_deck = ' '.join(p.deck.cards_in_deck[2:])
            discard = p.deck.cards_in_discard.split()
            treasure = [c for c in cards if c._is_treasure]
            not_treasure = [c for c in cards if not c._is_treasure]
            for c in not_treasure:
                discard.append(c._card_num)
            if treasure:
                socket.send({'user_action': 'stealing', 'player': p.player_num,
                        'cards': [[c.cardname, c._card_num] for c in treasure]})
            message = get_message(socket)
            for c in treasure:
                if not message.get('trash', -1) == c._card_num:
                    discard.append(c._card_num)
                if message.get('steal', -1) == c._card_num:
                    player.gain_card(c.cardname, from_stack=False)
            p.deck.cards_in_discard = ' '.join(discard)
            p.deck.save()


class ThroneRoom(ActionCard):
    def __init__(self, card_num):
        super(ThroneRoom, self).__init__(card_num)
        self._cost = 4
        self.cardname = 'ThroneRoom'

    def play_action(self, player, socket):
        socket.send({'user_action': 'pick_action'})
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
        # Give other players a curse.
        response_needed = set()
        for other in player.game.get_other_players():
            response_needed.add(other.player_num)
        socket.broadcast({'user_action': 'gain_curse',
                'attacking_player': player.player_num})
        while response_needed:
            message = get_message(socket)
            player_num = message['responding_player']
            other = player.game.player_set.get(player_num=player_num)
            if 'ok' in message:
                other.gain_card('Curse')
            elif 'moat' in message:
                pass
            response_needed.remove(message['responding_player'])


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
        socket.send({'user_action': 'gain_card_4'})
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
        'Moneylender': Moneylender,
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
