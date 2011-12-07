from django.db import models

class Game(models.Model):
    # For initial testing - to be removed
    name = models.CharField(max_length=128)
    num_players = models.IntegerField(default=4)
    current_player = models.IntegerField(default=1) # 1 based, not 0 based
    finished = models.BooleanField(default=False)
    log_file = models.CharField(max_length=128)

    def create_card_set(self, card_set):
        cardset = CardSet(game=self, name=card_set.name)
        cardset.save()
        for cardname in card_set.cards:
            card = get_card_from_name(cardname)
            num_cards = card.starting_stack_size(self.num_players)
            stack = CardStack(cardset=cardset, cardname=cardname,
                    num_cards=num_cards, num_left=num_cards)
            stack.save()

    def begin_game(self):
        """Initialize the players' decks and tell the first one it's his turn.

        This does _not_ create the CardSet for the game; that should be done
        elsewhere, when the game is created and before this method is called.
        """
        copper_stack = self.cardset.cardstack_set.get(cardname='Copper')
        estate_stack = self.cardset.cardstack_set.get(cardname='Estate')
        for player in self.player_set.all():
            for i in range(7):
                player.deck.add_card('Copper')
                copper_stack.num_left -= 1
            for i in range(3):
                player.deck.add_card('Estate')
                estate_stack.num_left -= 1
            player.end_turn()
        copper_stack.save()
        estate_stack.save()
        self.player_set.get(player_num=self.current_player).begin_turn()

    def get_other_players(self):
        return self.player_set.exclude(player_num=self.current_player)


class CardSet(models.Model):
    game = models.OneToOneField('Game')
    name = models.CharField(max_length=64)


class CardStack(models.Model):
    cardset = models.ForeignKey('CardSet')
    cardname = models.CharField(max_length=64)
    num_cards = models.IntegerField(default=10)
    num_left = models.IntegerField(default=10)


class Player(models.Model):
    TURN_STATES = (
            (u'NOTYOURTURN', u'Not your turn'),
            (u'ACTIONS', u'Play actions'),
            (u'BUY', u'Buy cards'),
            (u'WAITING', u'Waiting for others to respond to your action'),
            )
    game = models.ForeignKey('Game')
    name = models.CharField(max_length=64)
    human = models.BooleanField(default=True)
    player_num = models.IntegerField(default=1)
    connected = models.BooleanField(default=False)
    turn_state = models.CharField(max_length=32, choices=TURN_STATES)
    num_actions = models.IntegerField(default=1)
    num_buys = models.IntegerField(default=1)
    coins = models.IntegerField(default=0)
    waiting_for = models.TextField() # this is a JSON encoded string

    def begin_turn(self):
        # We don't reset coins here, because that's easiest to take care of
        # when we draw cards, which we do at the end of the turn.
        self.turn_state = TURN_STATES[1][0]
        self.num_actions = 1
        self.num_buys = 1
        self.save()

    def get_card_from_hand(self, card_num):
        hand = self.deck.cards_in_hand.split()
        if card_num not in hand:
            raise IllegalActionError("Cannot get card that isn't in hand")
        return self.card_from_card_num(card_num)

    def card_from_card_num(self, card_num):
        return get_card_from_name(
                self.deck.cards.get(card_num=card_num).cardname, card_num)

    def draw_card(self):
        card = self.deck.draw_card_to_hand()
        self.coins += card.coins()
        self.save()

    def discard_card(self, card_num):
        card = self.get_card_from_hand(card_num)
        self.coins -= card.coins()
        self.save()
        self.deck.discard_card_from_hand(card_num)

    def trash_card(self, card_num):
        card = self.get_card_from_hand(card_num)
        self.coins -= card.coins()
        self.save()
        self.deck.trash_card_from_hand(card_num)

    def play_action(self, card_num, socket):
        if self.turn_state == TURN_STATES[0][0]:
            raise IllegalActionError("It's not your turn!")
        elif self.turn_state == TURN_STATES[2][0]:
            raise IllegalActionError("You're in a buy state, you can't play "
            "actions")
        elif self.turn_state == TURN_STATES[3][0]:
            raise IllegalActionError("You need to wait for others to finish")
        self.deck.move_card_to_active_play(card_num)
        card = self.get_card_from_hand(card_num)
        # This method has the responsibility to change the state of the player
        # object, and to do whatever it needs to with other players.  It does
        # not necessarily need to save the player, as we do that here.
        card.play_action(self, socket)
        self.num_actions -= 1
        if self.num_actions == 0:
            self.turn_state = TURN_STATES[2][0]
        self.save()

    def buy_card(self, cardname):
        if self.turn_state == TURN_STATES[0][0]:
            raise IllegalActionError("It's not your turn!")
        elif self.turn_state == TURN_STATES[1][0]:
            self.turn_state = TURN_STATES[2][0]
        cardstack = self.game.cardset.cardstack_set.get(cardname=cardname)
        if cardstack.num_left == 0:
            raise IllegalActionError("Cannot buy a card from an empty stack")
        card = get_card_from_name(cardname)
        if self.coins < card.cost():
            raise IllegalActionError("Card costs more money than you have")
        self.coins -= card.cost()
        self.save()
        cardstack.num_left -= 1
        cardstack.save()
        self.deck.add_card(cardname)

    def gain_card(self, cardname):
        cardstack = self.game.cardset.cardstack_set.get(cardname=cardname)
        if cardstack.num_left == 0:
            raise IllegalActionError("Cannot buy a card from an empty stack")
        card = get_card_from_name(cardname)
        cardstack.num_left -= 1
        cardstack.save()
        self.deck.add_card(cardname)

    def end_turn(self):
        self.deck.discard_cards_in_hand()
        self.deck.discard_cards_in_play()
        self.deck.discard_active_cards_in_play()
        for i in range(5):
            self.draw_card()
        self.turn_state = TURN_STATES[0][0]
        self.save()


class Deck(models.Model):
    player = models.OneToOneField('Player')
    # These really should be lists (for cards_in_deck) or sets (for the
    # others), but you can't do that with a django model.  So instead these
    # will be space-delimited sequences of numbers, each number representing a
    # card in the deck.
    cards_in_hand = models.CharField(max_length=512)
    cards_in_deck = models.CharField(max_length=512)
    cards_in_discard = models.CharField(max_length=512)
    cards_in_play = models.CharField(max_length=512)
    active_cards_in_play = models.CharField(max_length=512)
    last_card_num = models.IntegerField(default=0)

    def get_num_cards(self):
        num_cards = 0
        num_cards += len(self.cards_in_hand.split())
        num_cards += len(self.cards_in_deck.split())
        num_cards += len(self.cards_in_discard.split())
        num_cards += len(self.cards_in_play.split())
        num_cards += len(self.active_cards_in_play.split())
        return num_cards

    def add_card(self, cardname):
        card = CardInDeck(deck=self, cardname=cardname,
                card_num=self.last_card_num+1)
        card.save()
        discard = self.cards_in_discard.split()
        discard.append(card.card_num)
        self.cards_in_discard = ' '.join(discard)
        self.last_card_num += 1
        self.save()

    def add_card_to_top_of_deck(self, cardname):
        card = CardInDeck(deck=self, cardname=cardname,
                card_num=self.last_card_num+1)
        card.save()
        deck = self.cards_in_deck.split()
        deck.insert(0, card.card_num)
        self.cards_in_deck = ' '.join(deck)
        self.last_card_num += 1
        self.save()

    def shuffle(self):
        """Takes cards_in_discard, shuffles them, and writes to cards_in_deck.

        cards_in_deck should be empty when this is called.  We enforce this by
        raising an IllegalActionError if the deck is not empty.
        """
        if len(cards_in_deck) != 0:
            raise IllegalActionError("Tried to shuffle when deck wasn't empty")
        cards = self.cards_in_discard.split()
        r = Random()
        r.shuffle(cards)
        self.cards_in_deck = ' '.join(cards)
        self.cards_in_discard = ''
        self.save()

    def get_cards_in_hand(self):
        """Returns a collection of Card objects representing those cards in
        hand."""
        hand = self.cards_in_hand.split()
        return [get_card_from_name(self.cards.get(card_num=h).cardname, h)
                for h in hand]

    def get_active_cards_in_play(self):
        """Returns a collection of Card objects representing those cards in
        play."""
        play = self.active_cards_in_play.split()
        return [get_card_from_name(self.cards.get(card_num=c).cardname, c)
                for c in play]

    def draw_card_to_hand(self):
        """Takes the top card off of the deck and puts it into cards_in_hand.

        If necessary, this shuffles the deck.
        """
        hand = self.cards_in_hand.split()
        deck = self.cards_in_deck.split()
        if not deck:
            self.shuffle()
            deck = self.cards_in_deck.split()
        card = deck[0]
        deck = deck[1:]
        hand.append(card)
        self.cards_in_hand = ' '.join(hand)
        self.cards_in_deck = ' '.join(deck)
        self.save()
        return card

    def draw_card_to_play(self):
        """Takes the top card off of the deck and puts it into cards_in_play.

        If necessary, this shuffles the deck.
        """
        play = self.cards_in_play.split()
        deck = self.cards_in_deck.split()
        if not deck:
            self.shuffle()
            deck = self.cards_in_deck.split()
        card = deck[0]
        deck = deck[1:]
        play.append(card)
        self.cards_in_play = ' '.join(play)
        self.cards_in_deck = ' '.join(deck)
        self.save()
        return card

    def move_card_to_active_play(self, card_num):
        play = self.active_cards_in_play.split()
        hand = self.cards_in_hand.split()
        hand.remove(card_num)
        play.append(card_num)
        self.active_cards_in_play = ' '.join(play)
        self.cards_in_hand = ' '.join(hand)
        self.save()

    def move_card_from_play_to_hand(self, card_num):
        play = self.cards_in_play.split()
        hand = self.cards_in_hand.split()
        play.remove(card_num)
        hand.append(card_num)
        self.cards_in_play = ' '.join(play)
        self.cards_in_hand = ' '.join(hand)
        self.save()

    def discard_cards_in_play(self):
        """Called at the end of turn.  Moves cards from play to discard."""
        play = self.cards_in_play.split()
        discard = self.cards_in_discard.split()
        discard.extend(play)
        self.cards_in_play = ''
        self.cards_in_discard = ' '.join(discard)
        self.save()

    def discard_active_cards_in_play(self):
        """Called at the end of turn.  Moves cards from play to discard."""
        play = self.active_cards_in_play.split()
        discard = self.cards_in_discard.split()
        discard.extend(play)
        self.active_cards_in_play = ''
        self.cards_in_discard = ' '.join(discard)
        self.save()

    def discard_cards_in_hand(self):
        """Called at the end of turn.  Moves cards from hand to discard."""
        hand = self.cards_in_hand.split()
        discard = self.cards_in_discard.split()
        discard.extend(hand)
        self.cards_in_hand = ''
        self.cards_in_discard = ' '.join(discard)
        self.save()

    def discard_card_from_hand(self, card_num):
        hand = self.cards_in_hand.split()
        discard = self.cards_in_discard.split()
        hand.remove(card_num)
        discard.append(card_num)
        self.cards_in_hand = ' '.join(hand)
        self.cards_in_discard = ' '.join(discard)
        self.save()


class CardInDeck(models.Model):
    deck = models.ForeignKey('Deck', related_name='cards')
    cardname = models.CharField(max_length=64)
    card_num = models.IntegerField(default=1)


class IllegalActionError(Exception):
    pass


def get_card_from_name(cardname, card_num=-1):
    classname = 'dominion.game.cards.' + cardname.replace(' ', '')
    cls = __import__(classname)
    return cls(card_num)
