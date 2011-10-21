# Create your views here.

from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from dominion.game.models import Game

def main(request):
    context = RequestContext(request)
    context['games'] = Game.objects.filter(finished=False)
    return render_to_response('main.html', context)


def new_game(request):
    game = Game(num_players=4)
    game.save()
    game.name = 'Game %d' % game.id
    game.save()
    return HttpResponseRedirect('/game/%d' % game.id)


def play(request, game):
    context = RequestContext(request)
    context['game'] = game
    return render_to_response('play.html', context)
