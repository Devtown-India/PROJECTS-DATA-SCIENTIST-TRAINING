import time
import logging

import spotipy
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView
from django.views.generic.edit import FormView, FormMixin

from ml import pipeline as ds, get_feat_playlists_new_albums
from .forms import PlaylistInputForm

# Create your views here.
from .models import Playlist, Song

logger = logging.getLogger("django")
logger.setLevel(logging.INFO)


def show_diverse_recs(res, threshold):
    """
    alternate cluster in recommendation so that songs are different genres/artists
    :param res:
    :param threshold:
    :return: df with subset of recs that are arranged with alternating cluster ids
    """
    rec_ids = []  # result list
    while len(rec_ids) < threshold:
        for clust in res["CENTROID"].unique():
            cluster_rec = res[res["CENTROID"] == clust]
            if len(rec_ids) < threshold:
                for i in cluster_rec.index:
                    if i in rec_ids:
                        continue
                    else:
                        rec = i
                        if rec not in rec_ids:
                            rec_ids.append(rec)  # add unique rec
                            break
                        else:
                            continue
            else:
                break
    # return subset of df with re-arranged items
    return res.loc[rec_ids]


User = get_user_model()


class PlaylistListFormView(LoginRequiredMixin, ListView, FormView, FormMixin):
    model = Playlist
    template_name = "index.html"
    queryset = Playlist.objects.all()
    form_class = PlaylistInputForm
    success_url = reverse_lazy("spotify_app:playlist_list")

    def get_context_data(self, **kwargs):
        get_feat_playlists_new_albums.main()  # get featured playlists on launch
        context = super().get_context_data(**kwargs)
        context["playlists"] = Playlist.objects.all().order_by("-date_created")[0:10]
        res = []
        try:
            for i, p in enumerate(context["playlists"]):
                if i < len(context["playlists"]) - 1:
                    if i % 3 == 0 or i == 0:
                        res.append((p, context["playlists"][i + 1], context["playlists"][i + 2]))
        except IndexError:
            logger.info("NO FEATURED PLAYLISTS RIGHT NOW")

        context["playlist_batches"] = res

        context["form"] = self.get_form()
        social = self.request.user.social_auth.get(provider="spotify")
        context["token"] = social.extra_data["access_token"]
        social.extra_data["spotify_me"] = spotipy.Spotify(auth=context["token"]).me()
        context["first_name"] = social.extra_data["spotify_me"]["display_name"].split()[0]
        #context["last_name"] = social.extra_data["spotify_me"]["display_name"].split('.')[1]
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            instance = form.save(commit=False)
            instance.playlist_id = instance.playlist_id.split("/")[-1]  # filter down to the playlist ID

            social = self.request.user.social_auth.get(provider="spotify")
            token = social.extra_data["access_token"]

            sp = spotipy.Spotify(auth=token)

            playlist = sp.playlist(playlist_id=instance.playlist_id)
            instance.playlist_name = playlist["name"]
            instance.playlist_url = playlist["external_urls"]["spotify"]
            instance.playlist_num_tracks = len(playlist["tracks"]["items"])
            instance.playlist_owner = playlist["owner"]["display_name"]
            instance.date_created = time.time()
            instance.save()
            return redirect("spotify_app:playlist_detail", playlist_id=instance.playlist_id)
        else:
            return self.form_invalid(form)


class ChosenPlaylistListView(ListView):
    template_name = "recommendations.html"
    model = Playlist
    playlist_id = None

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["chosen_playlist"] = Playlist.objects.get(playlist_id=self.kwargs["playlist_id"])

        return context


class RecommendationsView(ListView):
    template_name = "recommendations.html"
    model = Playlist

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["chosen_playlist"] = Playlist.objects.get(playlist_id=self.kwargs["playlist_id"])

        username = self.request.user.username

        logger.info(f"starting recommendations for {username}")

        social = self.request.user.social_auth.get(provider="spotify")
        token = social.extra_data["access_token"]

        try:
            recs = ds.main(playlist_id=context["chosen_playlist"].playlist_id, username=username, token=token)

            if recs.shape[0] > 5:  # order recommendations alternating clusters
                recs = show_diverse_recs(recs, 5)
            else:
                pass

            context["active_user"] = username
            sp = spotipy.Spotify(auth=token)
            social = self.request.user.social_auth.get(provider="spotify")
            context["token"] = social.extra_data["access_token"]
            social.extra_data["spotify_me"] = spotipy.Spotify(auth=context["token"]).me()
            context["first_name"] = social.extra_data["spotify_me"]["display_name"].split()[0]
            #context["last_name"] = social.extra_data["spotify_me"]["display_name"].split('.')[1]

            if recs.shape[0] > 0:
                logger.info("creating song db objects")
                logger.info(f"recommendations df shape {recs.shape}")

                rec_tracks = sp.tracks(recs.index.values)

                for i, rec in recs.iterrows():
                    tmp_song = Song()
                    tmp_song.song_id = i
                    tmp_song.song_name = rec_tracks["tracks"][recs.index.get_loc(i)]["name"]
                    tmp_song.artist_name = rec_tracks["tracks"][recs.index.get_loc(i)]["artists"][0]["name"]
                    tmp_song.song_is_explicit = recs.loc[i, :]["explicit"]
                    tmp_song.song_duration_ms = recs.loc[i, :]["duration_ms"]
                    tmp_song.recommended_user = username
                    tmp_song.date_created = time.time()
                    tmp_song.parent_playlist_id = context["chosen_playlist"].playlist_id
                    tmp_song.album_cover_art = rec_tracks["tracks"][recs.index.get_loc(i)]["album"]["images"][1][
                        "url"
                    ]
                    tmp_song.save()

                context["script_ran"] = True
                context["no_recommendations"] = False
            else:
                context["remove_rec_button"] = True
                context["no_recommendations"] = True
                logger.info("no recommendations!")

            logger.info(recs)
            if len(recs) > 5:
                context["recs"] = Song.objects.all().filter(
                    recommended_user=username, parent_playlist_id=context["chosen_playlist"].playlist_id
                )[:5]
            else:
                context["recs"] = Song.objects.all().filter(
                    recommended_user=username, parent_playlist_id=context["chosen_playlist"].playlist_id
                )

            return context

        except Exception as e:
            context["active_user"] = username
            sp = spotipy.Spotify(auth=token)
            social = self.request.user.social_auth.get(provider="spotify")
            context["token"] = social.extra_data["access_token"]
            social.extra_data["spotify_me"] = spotipy.Spotify(auth=context["token"]).me()
            context["first_name"] = social.extra_data["spotify_me"]["display_name"].split()[0]
            context["remove_rec_button"] = True
            #context["no_recommendations"] = True
            context["Zero_liked_songs"] = True
            logger.info("no recommendations!")
            return context

