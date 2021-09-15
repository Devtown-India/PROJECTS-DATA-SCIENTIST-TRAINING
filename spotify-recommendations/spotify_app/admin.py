from django.contrib import admin
from spotify_app.models import Playlist, Song, RecProfile

admin.site.register(Playlist)
admin.site.register(Song)
admin.site.register(RecProfile)
