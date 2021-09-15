import logging

import numpy as np
import pandas as pd
from funcy import chunks

logger = logging.getLogger('django')
logger.setLevel(logging.INFO)


def get_user_owned_playlist_contents(username, token, all_results, sp):
    """
    Function to get all songs from spotify playlists created by user

    Args:
        username (str): Spotify username
        token (str): Spotify api session token
        all_results (dict): empty dictionary
        sp: (Spotify object): Spotify API session object

    Returns:
        all_results (dictionary): dictionary with songs as keys and metadata as values
        df_master (Pandas DataFrame): DataFrame of all_results dictionary
    """

    # GET USER'S PLAYLISTS' CONTENTS

    if token:
        # get all user's created playlists
        playlists = sp.user_playlists(username)
        # iterate through all of the playlists
        for playlist in playlists["items"]:

            # filter only for playlists where the user is the owner, and filtering out some non-applicable playlists
            if (playlist["owner"]["id"] == username) & ("Archive" not in playlist["name"]):
                tracks = sp.user_playlist(username, playlist["id"], fields="tracks,next")["tracks"]

                tracks_total = tracks["items"]

                while tracks["next"]:
                    tracks = sp.next(tracks)  # get next page of tracks
                    tracks_total.extend(tracks["items"])  # extend master list

                for i in range(len(tracks_total)):
                    # get features/attributes of worth
                    song_id = tracks_total[i]["track"]["id"]

                    all_results[song_id] = {
                        "song_name": tracks_total[i]["track"]["name"],
                        "duration_ms": tracks_total[i]["track"]["duration_ms"],
                        "artist_name": tracks_total[i]["track"]["artists"][0]["name"],
                        "artist_id": tracks_total[i]["track"]["artists"][0]["id"],
                        "album_id": tracks_total[i]["track"]["album"]["id"],
                        "album_name": tracks_total[i]["track"]["album"]["name"],
                        "release_date": tracks_total[i]["track"]["album"]["release_date"],
                        "popularity": tracks_total[i]["track"]["popularity"],
                        "explicit": tracks_total[i]["track"]["explicit"],
                    }

        df_master = pd.DataFrame(all_results).T

        df_master = df_master.dropna()

        return all_results, df_master

    else:
        logging.info(f"Can't get token for {username}")


def get_user_saved_songs(username, token, all_results, sp):
    """
    Function to get all songs saved by a user

    Args:
        username (str): Spotify username
        token (str): Spotify api session token
        all_results (dict): dictionary with songs from get_user_owned_playlist_contents()
        sp: (Spotify object): Spotify API session object

    Returns:
        all_results (dictionary): dictionary with songs as keys and metadata as values, updated with saved songs
        df_master (Pandas DataFrame): DataFrame of all_results dictionary
    """

    if token:

        # GET USER'S SAVED SONGS

        saved_songs = sp.current_user_saved_tracks()  # get user's saved tracks
        saved_songs_total = saved_songs["items"]  # strip out the items

        while saved_songs["next"]:
            saved_songs = sp.next(saved_songs)  # get next page of tracks
            saved_songs_total.extend(saved_songs["items"])  # extend master list

        for i in range(len(saved_songs_total)):
            song_id = saved_songs_total[i]["track"]["id"]  # get song id
            # pdb.set_trace()
            if song_id not in all_results.keys():  # only get info for songs that aren't already in the list

                all_results[song_id] = {
                    "song_name": saved_songs_total[i]["track"]["name"],
                    "duration_ms": saved_songs_total[i]["track"]["duration_ms"],
                    "artist_name": saved_songs_total[i]["track"]["artists"][0]["name"],
                    "artist_id": saved_songs_total[i]["track"]["artists"][0]["id"],
                    "album_id": saved_songs_total[i]["track"]["album"]["id"],
                    "album_name": saved_songs_total[i]["track"]["album"]["name"],
                    "release_date": saved_songs_total[i]["track"]["album"]["release_date"],
                    "popularity": saved_songs_total[i]["track"]["popularity"],
                    "explicit": saved_songs_total[i]["track"]["explicit"],
                }

        # create dataframe from song data
        df_master = pd.DataFrame(all_results).T

        df_master = df_master.dropna()

        return all_results, df_master

    else:
        logging.info(f"Can't get token for {username}")


def get_deep_song_info(all_results, df_master, username, token, sp):
    """
    Get deep audio features for every song

    Args:
        all_results (dict): dictionary with songs from get_user_owned_playlist_contents()
        df_master (DataFrame): DF of all_results
        username (str): string of spotify username
        token (str): Spotify api session token
        sp: (Spotify object): Spotify API session object

    Returns:
        all_audio_features (dictionary): dictionary with songs as keys and deep song features as values
        df_master (Pandas DataFrame): df_master merged with deep audio features
    """
    if token:

        all_audio_features = dict()  # results dict for deep features

        # iterate through song ids in batches of 45
        for id_batch in chunks(45, all_results.keys()):
            # get audio features for batch
            try:
                batch_audio_features = sp.audio_features(id_batch)

                # create dictionary of song ids and features
                temp_dict = dict(zip(id_batch, batch_audio_features))

                # update main dictionary with results
                all_audio_features.update(temp_dict)
            except AttributeError:
                logger.info("ERROR AT {}".format(id_batch))
                continue

        # columns to drop
        drop_columns = ["duration_ms", "type", "analysis_url", "track_href", "uri", "id"]

        # create df from deep features and drop columns
        audio_features_df = pd.DataFrame(all_audio_features).T.drop(drop_columns, axis=1)

        # merge main df with deep df
        df_master = df_master.join(audio_features_df, on=df_master.index)
        return all_audio_features, df_master
    else:
        logging.info(f"Can't get token for {username}")


def get_album_info(df_master, username, token, sp):
    """
    Get album info for every song in df_master

    Args:
        df_master (DataFrame): DF returned from get_deep_song_info()
        username (str): string of spotify username
        token (str): Spotify api session token
        sp: (Spotify object): Spotify API session object

    Returns:
        albums_df (Pandas DataFrame): df with all album metadata/features
        df_master (Pandas DataFrame): df_master merged with albums_df/features
    """
    if token:

        all_albums = dict()  # results dict for album features

        # iterate in batches
        for album_id_batch in chunks(20, df_master["album_id"]):
            try:
                batch_albums = sp.albums(album_id_batch)  # get albums
                batch_albums = batch_albums["albums"]  # only pull out album info
                # iterate thorugh album ids
                for i, album_id in enumerate(album_id_batch):
                    # get only attributes of desire
                    all_albums[album_id] = {
                        "record_label": batch_albums[i]["label"],
                        "album_popularity": batch_albums[i]["popularity"],
                    }
            except AttributeError:
                logger.info("ERROR AT {}".format(album_id_batch))
                continue

        # create df of albums data
        albums_df = pd.DataFrame(all_albums).T

        # merge master df with album df
        df_master = df_master.join(albums_df, on="album_id")

        return albums_df, df_master
    else:
        logging.info(f"Can't get token for {username}")


def get_artist_info(df_master, username, token, sp):
    """
    Get artist info for every song in df_master

    Args:
        df_master (DataFrame): DF returned from get_album_info()
        username (str): string of spotify username
        token (str): Spotify api session token
        sp: (Spotify object): Spotify API session object

    Returns:
        artists_df (Pandas DataFrame): df with all artist metadata/features
        df_master (Pandas DataFrame): df_master merged with artists_df/features
    """
    if token:

        all_artists = dict()

        # iterate in batches

        for artist_id_batch in chunks(20, df_master["artist_id"].unique()):
            try:
                batch_artists = sp.artists(artist_id_batch)
                batch_artists = batch_artists["artists"]
                for i, artist_id in enumerate(artist_id_batch):
                    # get only attributes that are needed
                    all_artists[artist_id] = {
                        "artist_followers": batch_artists[i]["followers"]["total"],
                        "artist_genres": batch_artists[i]["genres"],
                        "artist_popularity": batch_artists[i]["popularity"],
                    }
            except AttributeError:
                logger.info("ERROR AT {}".format(artist_id_batch))

        # create df of artists data
        artists_df = pd.DataFrame(all_artists).T
        artists_df["artist_genres"] = artists_df.artist_genres.apply(
            lambda x: [i.replace(" ", "_") for i in x]
        )

        #######################################################################################################

        # merge master df with artists df
        df_master = df_master.join(artists_df, on="artist_id")

        return artists_df, df_master

    else:
        logging.info(f"Can't get token for {username}")


def get_playlist_tracks(username, playlist_id, sp):
    """
    Return tracks and metadata from Spotify playlist by playlist ID

    Args:
        username (str): string of spotify username
        playlist_id (str): string identifying Spotify playlist e.g. '37i9dQZF1DXcBWIGoYBM5M'
        sp: (Spotify object): Spotify API session object

    Returns:
        playlist_results (dictionary): dict with keys as songs and values as metadata
        playlist_df (Pandas DataFrame): df with all songs from playlist
    """
    playlist_results = dict()

    tracks = sp.user_playlist(username, playlist_id, fields="tracks,next")["tracks"]

    tracks_total = tracks["items"]

    while tracks["next"]:
        tracks = sp.next(tracks)  # get next page of tracks
        tracks_total.extend(tracks["items"])  # extend master list

    for i in range(len(tracks_total)):
        # get features/attributes of worth

        try:

            song_id = tracks_total[i]["track"]["id"]

            playlist_results[song_id] = {
                "song_name": tracks_total[i]["track"]["name"],
                "duration_ms": tracks_total[i]["track"]["duration_ms"],
                "artist_name": tracks_total[i]["track"]["artists"][0]["name"],
                "artist_id": tracks_total[i]["track"]["artists"][0]["id"],
                "album_id": tracks_total[i]["track"]["album"]["id"],
                "album_name": tracks_total[i]["track"]["album"]["name"],
                "release_date": tracks_total[i]["track"]["album"]["release_date"],
                "popularity": tracks_total[i]["track"]["popularity"],
                "explicit": tracks_total[i]["track"]["explicit"],
            }
        except TypeError:
            logging.info("error at {}".format(i))
    playlist_df = pd.DataFrame(playlist_results).T
    return playlist_results, playlist_df


def clean_data(df_master):
    """
    Return cleaned and trimmed dataframe, removing columns
    and creating features in addition to setting consistent datatypes

    Args:
        df_master (pandas DataFrame): df returned from any of functions above

    Returns:
        df_features (pandas DataFrame): df with removed unimportant columns, new features, and dummy variables
    """

    high_level_genres = [
        "hip_hop",
        "pop",
        "rap",
        "electro",
        "edm",
        "metal",
        "chill",
        "choral",
        "blues",
        "broadway",
        "christmas",
        "punk",
        "dance",
        "deep",
        "disco",
        "dubstep",
        "grunge",
        "funk",
        "gospel",
        "latin",
        "lo-fi",
        "techno",
        "guitar",
        "soul",
        "jazz",
        "country",
        "piano",
        "drift",
        "sleep",
        "grime",
        "indie",
        "alt",
        "ambient",
        "r&b",
        "folk",
        "background_music",
        "classical",
        "rock",
        "trap",
        "singer-songwriter",
    ]

    df_features = df_master.copy(deep=True)  # copy dataframe

    #     df_features[high_level_genres] = 0es

    for genre in high_level_genres:
        df_features[genre] = (
            df_features["artist_genres"]
            .astype(str)
            .str.contains(genre, na=False, regex=True)
            .astype(int)
        )

    df_features = pd.concat(
        [
            df_features,
            pd.get_dummies(df_features["time_signature"], prefix="time_signature"),
        ],
        axis=1,
    )  # create dummies for time_signature column

    df_features = df_features.drop(
        [
            "release_date",
            "song_name",
            "time_signature",
            "album_popularity",
            "popularity",
            "album_name",
            "key",
            "record_label",
            "album_id",
            "artist_id",
            "artist_genres",
            "artist_name",
            "artist_followers",
            "artist_popularity"
        ],
        axis=1,
    )  # drop all un-needed columns

    # drop all rows that have at least one null value
    df_features = df_features.dropna()

    for col in [
        "duration_ms",
        "explicit",
        "acousticness",
        "danceability",
        "energy",
        "instrumentalness",
        "liveness",
        "loudness",
        "mode",
        "speechiness",
        "tempo",
        "valence",
    ]:
        # ensure that all columns have consistent datatypes
        df_features[col] = df_features[col].apply(float)

    return df_features


def make_dfs_comparable(df_features, df_playlist_features):
    """
    Returns dataframe with same columns as the training dataframe

    Args:
        df_features (pandas DataFrame): features df used for training the classifier
        df_playlist_features (pandas DataFrame): playlist features df - from one playlist


    Returns:
        df_playlist_features (pandas DataFrame): df with columns added/removed to match the df_features df
    """

    # need to make sure that the playlist df has the same columns as the training df

    # create dummy columns to match training df, set all values to zero
    for col in np.setdiff1d(df_features.columns, df_playlist_features.columns):
        df_playlist_features[col] = 0

    # compare the other way around, create columns and set their values to zero
    for col in np.setdiff1d(df_playlist_features.columns, df_features.columns):
        df_playlist_features[col] = 0

    # drop columns that appear in the playlist df but not in the training df
    for col in np.setdiff1d(df_playlist_features.columns, df_features.columns):
        df_playlist_features = df_playlist_features.drop(col, axis=1)

    # drop columns that appear in the playlist df but not in the training df
    for col in np.setdiff1d(df_features.columns, df_playlist_features.columns):
        df_playlist_features = df_playlist_features.drop(col, axis=1)

    return df_playlist_features
