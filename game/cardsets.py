#!/usr/bin/env python

all_cards = set(('Copper', 'Silver', 'Gold', 'Estate', 'Duchy', 'Province',
        'Curse', 'Gardens', 'Adventurer', 'Bureaucrat', 'Cellar', 'Chancellor',
        'Chapel', 'CouncilRoom', 'Feast', 'Festival', 'Laboratory', 'Library',
        'Market', 'Militia', 'Mine', 'Moat', 'MoneyLender', 'Remodel',
        'Smithy', 'Spy', 'Thief', 'ThroneRoom', 'Village', 'Witch',
        'Woodcutter', 'Workshop'))


class BaseCardSet(object):
    def __init__(self):
        self.cards = set(('Copper', 'Silver', 'Gold', 'Estate', 'Duchy',
                'Province', 'Curse'))


class RandomCardSet(BaseCardSet):
    def __init__(self):
        super(RandomCardSet, self).__init__()
        self.name = 'Random'
        from random import Random
        r = Random()
        cards_left = all_cards - self.cards
        for i in range(10):
            card = r.choice(cards_left)
            cards_left.remove(card)
            self.cards.add(card)


class FirstGameCardSet(BaseCardSet):
    def __init__(self):
        super(FirstGameCardSet, self).__init__()
        self.name = 'First Game'
        cards = set(['Cellar', 'Market', 'Militia', 'Mine', 'Moat', 'Remodel',
                'Smithy', 'Village', 'Woodcutter', 'Workshop'])
        self.cards.update(cards)


class BigMoneyCardSet(BaseCardSet):
    def __init__(self):
        super(BigMoneyCardSet, self).__init__()
        self.name = 'Big Money'
        cards = set(['Adventurer', 'Bureaucrat', 'Chancellor', 'Chapel',
                'Feast', 'Laboratory', 'Market', 'Mine', 'Moneylender',
                'Throne Room'])
        self.cards.update(cards)


class InteractionCardSet(BaseCardSet):
    def __init__(self):
        super(InteractionCardSet, self).__init__()
        self.name = 'Interaction'
        cards = set(['Bureaucrat', 'Chancellor', 'Council Room', 'Festival',
                'Library', 'Militia', 'Moat', 'Spy', 'Thief', 'Village'])
        self.cards.update(cards)


class SizeDistortionCardSet(BaseCardSet):
    def __init__(self):
        super(SizeDistortionCardSet, self).__init__()
        self.name = 'Size Distortion'
        cards = set(['Cellar', 'Chapel', 'Feast', 'Gardens', 'Laboratory',
                'Thief', 'Village', 'Witch', 'Woodcutter', 'Workshop'])
        self.cards.update(cards)


class VillageSquareCardSet(BaseCardSet):
    def __init__(self):
        super(VillageSquareCardSet, self).__init__()
        self.name = 'Village Square'
        cards = set(['Bureaucrat', 'Cellar', 'Festival', 'Library', 'Market',
                'Remodel', 'Smithy', 'Throne Room', 'Village', 'Woodcutter'])
        self.cards.update(cards)


# vim: et sw=4 sts=4
