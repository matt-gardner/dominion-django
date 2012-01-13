import os
from django.conf.urls.defaults import *
from django.conf import settings

game = '(?P<game>[^/]+)'
player = '(?P<player>[^/]+)'

urlpatterns = patterns('',
    (r'^$', 'game.views.game.main'),
    (r'^new-game/$', 'game.views.game.new_game'),
    (r'^game/' + game + '$', 'game.views.game.pick_player'),
    (r'^game/' + game + '/player/' + player + '$', 'game.views.game.play'),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve',
                {'document_root': os.path.join(settings.BASE_PATH, 'media')}),
)

urlpatterns += patterns('',
    (r'^socket\.io', 'game.views.socketio.socketio'),
)
