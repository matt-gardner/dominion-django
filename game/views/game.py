# Create your views here.

from django import forms
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from dominion.game.models import Deck, Game, CardSet, CardStack
from dominion.game.models import get_card_from_name
from dominion.game import cardsets

def main(request):
    context = RequestContext(request)
    context['games'] = Game.objects.filter(finished=False)
    return render_to_response('main.html', context)


def new_game(request):
    context = RequestContext(request)
    context['form'] = NewGameForm()
    return render_to_response('new_game.html', context)


@transaction.commit_manually
def create_new_game(request):
    form = NewGameForm(request.POST)
    if not form.is_valid():
        # Not too good yet
        return HttpResponseRedirect('main.html')
    num_players = 2
    game = Game(num_players=num_players)
    game.save()
    for i in range(1, num_players+1):
        game.player_set.create(player_num=i, name='Player %d' % i)
        player = game.player_set.get(player_num=i)
        player.deck = Deck()
        player.deck.save()
    game.name = 'Game %d' % game.id
    game.save()
    cardset_name = form.cleaned_data['cardset']
    print cardset_name
    cardset = cardsets.from_name[cardset_name]()
    game.cardset = CardSet(game=game, name=cardset.name)
    game.cardset.save()
    for cardname in cardset.cards:
        card = get_card_from_name(cardname)
        num = card.starting_stack_size(num_players)
        game.cardset.cardstack_set.create(cardname=cardname, num_cards=num,
                num_left=num)
    game.begin_game()
    transaction.commit()
    return HttpResponseRedirect('/game/%d' % game.id)


def pick_player(request, game):
    context = RequestContext(request)
    game = Game.objects.get(pk=game)
    context['game'] = game
    return render_to_response('pick_player.html', context)

def play(request, game, player):
    context = RequestContext(request)
    game = Game.objects.get(pk=game)
    context['game'] = game
    player = game.player_set.get(player_num=player)
    context['player'] = player
    return render_to_response('play.html', context)

class NewGameForm(forms.Form):
    cardset = forms.ChoiceField((x,x) for x in cardsets.from_name.keys())
