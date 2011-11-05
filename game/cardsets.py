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
        super(self, RandomCardSet).__init__()
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
        super(self, SelectedCardSet).__init__()
        self.name = 'First Game'
        raise NotFinishedError()


# vim: et sw=4 sts=4
