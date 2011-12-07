# Create your views here.

from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from dominion.game.models import Game, CardSet, CardStack
from dominion.game.models import get_card_from_name
from dominion.game.cardsets import *

def main(request):
    context = RequestContext(request)
    context['games'] = Game.objects.filter(finished=False)
    return render_to_response('main.html', context)


def new_game(request, cardset=None):
    num_players = 2
    game = Game(num_players=num_players)
    game.save()
    game.name = 'Game %d' % game.id
    game.save()
    if not cardset:
        cardset = FirstGameCardSet()
    game.cardset = CardSet(game=game, name=cardset.name)
    game.cardset.save()
    for cardname in cardset.cards:
        card = get_card_from_name(cardname)
        num = card.starting_stack_size(num_players)
        game.cardset.cardstack_set.create(cardname=cardname, num_cards=num,
                num_left=num)
    return HttpResponseRedirect('/game/%d' % game.id)


def play(request, game):
    context = RequestContext(request)
    context['game'] = game
    return render_to_response('play.html', context)
