from django.db import models

class Game(models.Model):
    name = models.CharField(max_length=128)
    num_players = models.IntegerField(default=4)
    current_player = models.IntegerField(default=1) # 1 based, not 0 based
    finished = models.BooleanField(default=False)
    log_file = models.CharField(max_length=128)

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
    num_cards = models.IntegerField(defualt=10)
    num_left = models.IntegerField(defualt=10)


class Player(models.Model):
    TURN_STATES = (
            (u'NOTYOURTURN', u'Not your turn'),
            (u'ACTIONS', u'Play actions'),
            (u'BUY', u'Buy cards')
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

    def begin_turn(self):
        self.turn_state = TURN_STATES[1]
        self.num_actions = 1
        self.num_buys = 1
        self.coins = self.get_coin_count()
        self.save()

    def play_action(self, card_num):
        if self.turn_state == TURN_STATES[0][0]:
            raise IllegalActionError("It's not your turn!")
        elif self.turn_state == TURN_STATES[2][0]:
            raise IllegalActionError("You're in a buy state, you can't play "
            "actions")
        hand = self.deck.cards_in_hand.split()
        if card_num not in hand:
            raise IllegalActionError("Cannot play card that isn't in hand")
        card = get_card_from_name(
                self.deck.cards.get(card_num=card_num).cardname)
        # This method has the responsibility to change the state of the player
        # object, and to do whatever it needs to with other players.  It does
        # not necessarily need to save the player, as we do that here.
        card.play_action(self)
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

    def get_coin_count(self):
        hand = self.deck.get_cards_in_hand()
        coins = 0
        for card in hand:
            coins += card.coins()
        return coins

    def end_turn(self):
        self.deck.discard_cards_in_hand()
        self.deck.discard_cards_in_play()
        self.deck.discard_active_cards_in_play()
        for i in range(5):
            self.deck.draw_card_to_hand()
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

    def add_card(self, cardname):
        card = CardInDeck(deck=self, cardname=cardname,
                card_num=self.last_card_num+1)
        card.save()
        discard = self.cards_in_discard.split()
        discard.append(card.card_num)
        self.cards_in_discard = ' '.join(discard)
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
        return [get_card_from_name(self.cards.get(card_num=h).cardname)
                for h in hand]

    def get_active_cards_in_play(self):
        """Returns a collection of Card objects representing those cards in
        play."""
        play = self.active_cards_in_play.split()
        return [get_card_from_name(self.cards.get(card_num=c).cardname)
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
        hand.append(deck[0])
        deck = deck[1:]
        self.cards_in_hand = ' '.join(hand)
        self.cards_in_deck = ' '.join(deck)
        self.save()

    def draw_card_to_play(self):
        """Takes the top card off of the deck and puts it into cards_in_play.

        If necessary, this shuffles the deck.

        We also return the card from this method for easy access by the caller.
        """
        play = self.cards_in_play.split()
        deck = self.cards_in_deck.split()
        if not deck:
            self.shuffle()
            deck = self.cards_in_deck.split()
        play.append(deck[0])
        deck = deck[1:]
        self.cards_in_play = ' '.join(play)
        self.cards_in_deck = ' '.join(deck)
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


class CardInDeck(models.Model):
    deck = models.ForeignKey('Deck', related_name='cards')
    cardname = models.CharField(max_length=64)
    card_num = models.IntegerField(default=1)


class IllegalActionError(Exception):
    pass
