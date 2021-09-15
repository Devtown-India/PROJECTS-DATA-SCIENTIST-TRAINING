import sys
import logging

import spotipy.oauth2
from sklearn.preprocessing import MinMaxScaler
from django.contrib.auth.models import User
from spotify_app.models import RecProfile
import pandas as pd
from hdbscan import HDBSCAN
import hdbscan

from ml.helper_functions import (
    get_album_info,
    get_deep_song_info,
    get_playlist_tracks,
    clean_data,
    make_dfs_comparable,
    get_artist_info,
    get_user_owned_playlist_contents,
    get_user_saved_songs,
)

logger = logging.getLogger('django')
logger.setLevel(logging.INFO)


def get_recommendations(username, playlist_id, sp, token, df_features, hdbs, scaler):
    """
    :param username: spotify username
    :param playlist_id: selected playlist id
    :param sp: connected spotipy object to get api data
    :param token: token used to verify user info with spotify
    :param df_features: df of features for comparison with recs
    :param hdbs: saved hsbscan object saved from training
    :param scaler: saved MinMaxScaler object fit on training data
    :return: recs - df of recommendations
    """
    logger.info("getting playlist tracks for selected playlist")
    # get all songs from selected playlist
    playlist_results, playlist_df = get_playlist_tracks(username, playlist_id, sp)

    logger.info("getting deep info for selected playlist")
    # get deep song info from playlist songs
    playlist_results, playlist_df = get_deep_song_info(playlist_results, playlist_df, username, token, sp)

    logger.info("getting album info for selected playlist")
    # get album info for all songs in that playlist
    playlist_results, playlist_df = get_album_info(playlist_df, username, token, sp)

    logger.info("getting artist info for selected playlist")
    # get artist info for all songs in that playlist
    playlist_results, playlist_df = get_artist_info(playlist_df, username, token, sp)

    logger.info("cleaning selected playlist data")
    df_playlist_features = clean_data(playlist_df)  # return a cleaned df with more features

    df_playlist_features = make_dfs_comparable(
        df_features, df_playlist_features
    )  # make df playlist columns match training data

    # create a dataframe from the scaled data
    playlist_scaled = scaler.transform(df_playlist_features)
    playlist_scaled = pd.DataFrame(
        playlist_scaled,
        columns=df_playlist_features.columns,
        index=df_playlist_features.index)

    playlist_labels = hdbscan.approximate_predict(hdbs, playlist_scaled)  # classify on playlist songs

    df_playlist_features["CENTROID"] = playlist_labels[0]  # add centroid to original features df
    df_playlist_features["PROBABILITY"] = playlist_labels[1]  # add cluster probabilities

    res = df_playlist_features[
        (~df_playlist_features.index.isin(df_features.index)) &
        (df_playlist_features['CENTROID'] != -1)]  # SONGS THAT MATCH THE CLASSIFIER

    res = res.sort_values(
        by=["PROBABILITY"], ascending=False
    )  # sort results by probability, then by pop

    return res


def main(playlist_id, username, token):
    current_user = User.objects.get(username=username)
    sp = spotipy.Spotify(auth=token)  # create spotify object

    try:
        prof_obj = RecProfile.objects.get(user=current_user)
    except RecProfile.DoesNotExist:
        prof = RecProfile()
        prof.user = current_user
        prof.save()
        prof_obj = RecProfile.objects.get(user=current_user)

    if prof_obj.user_has_objects is not True:
        logger.info("USING NEW DATA TO MAKE RECOMMENDATIONS")
        all_results = dict()

        logger.info("getting playlists")

        all_results = get_user_owned_playlist_contents(username, token, all_results, sp)[
            0
        ]  # get playlist contents

        logger.info("getting user saved songs")
        all_results, df_master = get_user_saved_songs(
            username, token, all_results, sp
        )  # get user saved songs

        logger.info("getting deep features for songs")
        all_results, df_master = get_deep_song_info(
            all_results, df_master, username, token, sp
        )  # get deep song info from combined songs

        logger.info("getting album info")
        albums_df, df_master = get_album_info(
            df_master, username, token, sp
        )  # get album info for all unique albums from df_master

        logger.info("getting artist info")
        artists_df, df_master = get_artist_info(
            df_master, username, token, sp
        )  # get artist info for all unique artists from df_master
        df_features = clean_data(df_master)  # clean data and return df with more features

        train_scaler = MinMaxScaler().fit(df_features)
        X_train_scaled = train_scaler.transform(df_features)

        # create a dataframe from the scaled data
        X_train_scaled = pd.DataFrame(
            X_train_scaled, columns=df_features.columns, index=df_features.index)

        logger.info("df shape is {}".format(X_train_scaled.shape))

        logger.info("=> fitting HDBSCAN object")
        # create hdbscan classifier fit on the PCA_df
        hdbs = HDBSCAN(
            prediction_data=True,
            core_dist_n_jobs=4,
            min_samples=1,
            min_cluster_size=2,
            leaf_size=2,
            cluster_selection_epsilon=0.5).fit(X_train_scaled)

        prof_obj.user_hdbscan = hdbs
        prof_obj.user_train_scaler = train_scaler
        prof_obj.user_df_features_obj = df_features
        prof_obj.user_df_scaled_obj = X_train_scaled
        prof_obj.user_has_objects = True
        prof_obj.user_has_objects = True
        prof_obj.save()

        recs = get_recommendations(
            username,
            playlist_id=playlist_id,
            sp=sp,
            token=token,
            df_features=df_features,
            hdbs=hdbs,
            scaler=train_scaler,
        )

    else:
        logger.info("USING STORED DATA TO MAKE RECOMMENDATIONS")
        recs = get_recommendations(
            username,
            playlist_id=playlist_id,
            sp=sp,
            token=token,
            df_features=prof_obj.user_df_features_obj,
            hdbs=prof_obj.user_hdbscan,
            scaler=prof_obj.user_train_scaler,
        )

    return recs


if __name__ == "__main__":
    main(playlist_id=sys.argv[1], username=sys.argv[2])
