from django.contrib import admin
from django.urls import path, include
from . import views

app_name = "spotify_app"

urlpatterns = [
    path("playlists/", views.PlaylistListFormView.as_view(), name="playlist_list"),
    path("playlists/<playlist_id>", views.ChosenPlaylistListView.as_view(), name="playlist_detail"),
    path("playlists/<playlist_id>/recommend", views.RecommendationsView.as_view(), name="recommendations"),
]
