# shows a user's playlists (need to be authenticated via oauth)

import sys
import os
import spotipy
import subprocess
import numpy as np
import pprint as pp
import spotipy.util as util
from nltk.metrics import masi_distance, edit_distance

def weighted_avg_edit_distance(phrase1, phrase2):
    '''

    Custom distance metric for comparing two phrases, developed by Alex.

    Intended for comparing a known phrase with a speech transcription.
    Uses the assumption that AT LEAST one transcribed word is spelled similarly to another in the known phrase.

    Returns a distance value between 0 and 1

    '''

    word_set1 = set(str(phrase1).split())
    word_set2 = set(str(phrase2).split())

    # Exhaustive search for minumum edit_distance between all words in each string
    word_min_edit_distances = [np.amin([edit_distance(word1, word2) for word2 in list(word_set2)]) for word1 in list(word_set1)]

    # Take weighted average of the min_edit_distance
    # Compute reciprocal so that words with lower distance get a higher weight in the average
    weights = 1.0 / (np.asarray(word_min_edit_distances) + 1e-6)
    return np.average(word_min_edit_distances, weights=weights)

def spotify_playlist_control(username, action='play', plalist_search_str=None):
    assert action in ['play', 'pause', 'unpause', 'toggle_playback'], 'Parameter action not valid'
    
    token = util.prompt_for_user_token(username)

    if not token:
        print("Can't get token for", username)
        return
    sp = spotipy.Spotify(auth=token)
    
    if action == 'play':
        assert plalist_search_str is not None
    else:
        subprocess.call(['spotify-remote', action])
        return
    
    playlists = sp.user_playlists(username)
    playlist_names = [x['name'] for x in playlists['items']]

    distance_results = []
    for text in playlist_names:
        playlist_name = ''.join([i if ord(i) < 128 else '' for i in text]).lower()

        d1 = weighted_avg_edit_distance(playlist_name, plalist_search_str)
        distance_results.append((text, d1))

    sorted_playlists = sorted(distance_results, key=lambda x:x[1])
    pp.pprint(sorted_playlists)

    for playlist in playlists['items']:
        if playlist['name'] == sorted_playlists[0][0]:
            print(playlist['name'])
            subprocess.call(['spotify-remote', action, playlist['uri']])

if __name__ == '__main__':
    if len(sys.argv) > 2:
        username = sys.argv[1]
        action = sys.argv[2]
        
        try:
            playlist_search_term = sys.argv[3]
        except IndexError:
            playlist_search_term = None
 
        print(username, action, playlist_search_term)

    else:
        print("usage: python magicmirror_spotify_control.py [username] [action] ?[playlist search term]")
        sys.exit()

    spotify_playlist_control(username, action, playlist_search_term)