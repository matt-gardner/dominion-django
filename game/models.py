from django.db import models

class Game(models.Model):
    name = models.CharField(max_length=128)
    num_players = models.IntegerField(default=4)
    finished = models.BooleanField(default=False)
    count = models.IntegerField(default=0)
