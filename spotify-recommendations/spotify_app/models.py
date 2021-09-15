from django.conf import settings
from django.db import models
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from picklefield.fields import PickledObjectField


class Playlist(models.Model):
    class Meta:
        app_label = "spotify_app"

    playlist_id = models.CharField(max_length=120, primary_key=True)
    playlist_name = models.TextField(max_length=100)
    playlist_url = models.CharField(max_length=1000)
    playlist_num_tracks = models.IntegerField(null=True)
    playlist_featured = models.BooleanField(default=False)
    playlist_owner = models.CharField(max_length=500)
    date_created = models.CharField(max_length=500, default="No date")
    playlist_img_src = models.CharField(max_length=5000, null=True, default="no_img")

    def __str__(self):
        return self.playlist_name


class Song(models.Model):
    class Meta:
        app_label = "spotify_app"

    song_id = models.CharField(max_length=120, primary_key=True)
    song_name = models.TextField(blank=False, null=False)
    artist_name = models.CharField(max_length=120, blank=False, null=False)
    song_is_explicit = models.BooleanField(blank=False)
    song_duration_ms = models.IntegerField(blank=False)
    recommended_user = models.CharField(blank=False, max_length=500)
    date_created = models.CharField(max_length=500, default="No date")
    parent_playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, db_column="parent_playlist_id")
    album_cover_art = models.CharField(max_length=5000, null=True, default="no_img")

    def __str__(self):
        return self.song_name


class RecProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    user_hdbscan = PickledObjectField(null=True, default="no_object_yet")
    user_train_scaler = PickledObjectField(null=True, default="no_object_yet")
    user_df_features_obj = PickledObjectField(null=True, default="no_object_yet")
    user_df_scaled_obj = PickledObjectField(null=True, default="no_object_yet")
    user_top_clusters_obj = PickledObjectField(null=True, default="no_object_yet")
    user_has_objects = models.BooleanField(default=False, null=True)

    def __str__(self):
        return self.user.username

    def validate_unique(self, exclude=None):
        super().validate_unique(exclude="host")
