import django
import os
import logging

from spotipy.oauth2 import SpotifyClientCredentials

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "spotify_recs.settings")
django.setup()
from spotify_app.models import Playlist
import spotipy
import time

logger = logging.getLogger('django')
logger.setLevel(logging.INFO)


def main():
    client_credentials_manager = SpotifyClientCredentials(
        client_id="fd2ae3d3b2d3407da3b02a97376827b5", client_secret="e84c4e18dd2f463aa0c649341d64dbfb"
    )
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    logger.info("Getting featured playlists...")

    payload = sp.featured_playlists()["playlists"]

    playlist_total = payload["items"]

    while payload["next"]:
        payload = sp.next(payload)
        playlist_total.extend(payload["items"])

    for playlist in playlist_total:
        temp_obj = Playlist(
            playlist_id=playlist["id"],
            playlist_name=playlist["name"],
            playlist_url=playlist["external_urls"]["spotify"],
            playlist_num_tracks=playlist["tracks"]["total"],
            playlist_featured=True,
            playlist_owner=playlist["owner"]["display_name"].lower(),
            date_created=time.time(),
            playlist_img_src=playlist["images"][0]["url"],
        )
        temp_obj.save()


if __name__ == "__main__":
    main()
