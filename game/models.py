from django.db import models

class Game(models.Model):
    name = models.CharField(max_length=128)
    num_players = models.IntegerField(default=4)
    # 1 based, not 0 based
    current_player = models.IntegerField(default=1)
    finished = models.BooleanField(default=False)
    count = models.IntegerField(default=0)


class Player(models.Model):
    game = models.ForeignKey('Game')
    player_num = models.IntegerField(default=1)
    connected = models.BooleanField(default=False)
