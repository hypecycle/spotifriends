import base64
import json
import requests
import urllib.request, urllib.parse, urllib.error
import logging

'''
    --------------------- HOW THIS FILE IS ORGANIZED --------------------
    0. SPOTIFY BASE URL
    1. USER AUTHORIZATION
    2. ARTISTS
    3. SEARCH
    4. USER RELATED REQUETS (NEEDS OAUTH)
    5. ALBUMS
    6. USERS
    7. TRACKS
    8. BROWSE (added)
'''
# -------------------- Prepare for logging -------------

# create logger with 'spotify_app'
logging.basicConfig(filename="spotify_app.log", level=logging.INFO,
    format="%(asctime)s:%(levelname)s:%(message)s"
    )

# ----------------- 0. SPOTIFY BASE URL ----------------

SPOTIFY_API_BASE_URL = 'https://api.spotify.com'
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)

# ----------------- 1. USER AUTHORIZATION ----------------

# spotify endpoints
SPOTIFY_AUTH_BASE_URL = "https://accounts.spotify.com/{}"
SPOTIFY_AUTH_URL = SPOTIFY_AUTH_BASE_URL.format('authorize')
SPOTIFY_TOKEN_URL = SPOTIFY_AUTH_BASE_URL.format('api/token')

# client keys
CLIENT = json.load(open('conf.json', 'r+'))
CLIENT_ID = CLIENT['id']
CLIENT_SECRET = CLIENT['secret']
CLIENT_SIDE_URL = CLIENT['url']
PORT = CLIENT['port']


# server side parameter
# * fell free to change it if you want to, but make sure to change in
# your spotify dev account as well *
#CLIENT_SIDE_URL = "http://ddns.buzztelecke.de"
#PORT = 81
REDIRECT_URI = "{}:{}/callback/".format(CLIENT_SIDE_URL, PORT)
#REDIRECT_URI = "{}/callback/".format(CLIENT_SIDE_URL)
SCOPE = "playlist-modify-public playlist-modify-private user-read-recently-played user-top-read"
STATE = ""
SHOW_DIALOG_bool = True
SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()

# https://developer.spotify.com/web-api/authorization-guide/
auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    # "state": STATE,
    # "show_dialog": SHOW_DIALOG_str,
    "client_id": CLIENT_ID
}

URL_ARGS = "&".join(["{}={}".format(key, urllib.parse.quote(val))
                    for key, val in auth_query_parameters.items()])
AUTH_URL = "{}/?{}".format(SPOTIFY_AUTH_URL, URL_ARGS)

'''
    This function must be used with the callback method present in the
    ../app.py file.
    And of course this will only works if ouath == True
'''


def authorize(auth_token):

    code_payload = {
        "grant_type": "authorization_code",
        "code": str(auth_token),
        "redirect_uri": REDIRECT_URI
    }

    base64encoded = base64.b64encode(("{}:{}".format(CLIENT_ID, CLIENT_SECRET)).encode()).decode("utf-8")

    #Log
    logging.info("code_payload: {}".format(code_payload))

    headers = {"Authorization": "Basic {}".format(base64encoded)}

    post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload,
                                 headers=headers)
    #Log
    logging.info("headers: {}".format(headers))

    # tokens are returned to the app
    response_data = json.loads(post_request.text)

    logging.info("response_data payload: {}".format(response_data))
    
    if response_data:

        access_token = response_data["access_token"]
        # use the access token to access Spotify API
        auth_header = {"Authorization": "Bearer {}".format(access_token)}
    else:
        auth_header = {}
        
    return auth_header

# ---------------- 2. ARTISTS ------------------------
# https://developer.spotify.com/web-api/artist-endpoints/

GET_ARTIST_ENDPOINT = "{}/{}".format(SPOTIFY_API_URL, 'artists')  # /<id>



# https://developer.spotify.com/web-api/get-artists-albums/
def get_artists_albums(artist_id):
    url = "{}/{id}/albums".format(GET_ARTIST_ENDPOINT, id=artist_id)
    resp = requests.get(url)
    return resp.json()

# https://developer.spotify.com/web-api/get-artists-top-tracks/
def get_artists_top_tracks(artist_id, country='US'):
    url = "{}/{id}/top-tracks".format(GET_ARTIST_ENDPOINT, id=artist_id)
    myparams = {'country': country}
    resp = requests.get(url, params=myparams)
    return resp.json()

# update mit auth:	
# https://developer.spotify.com/web-api/get-related-artists/
def get_related_artists(auth_header, artist_id):
    url = "{}/{id}/related-artists".format(GET_ARTIST_ENDPOINT, id=artist_id)
    resp = requests.get(url, headers=auth_header)
    return resp.json()
    
# update mit auth:
# https://developer.spotify.com/web-api/get-artist/
def track_artist_features(auth_header, artist_id):
	url = "{}/{id}".format(GET_ARTIST_ENDPOINT, id=artist_id)
	resp = requests.get(url, headers=auth_header)
	return resp.json()

# update mit auth:	
# https://developer.spotify.com/web-api/get-several-artists/
def get_several_artists(auth_header, list_of_ids):
    url = "{}/?ids={ids}".format(GET_ARTIST_ENDPOINT, ids=','.join(list_of_ids))
    resp = requests.get(url, headers=auth_header)
    return resp.json()



# ----------------- 3. SEARCH ------------------------
# https://developer.spotify.com/web-api/search-item/

SEARCH_ENDPOINT = "{}/{}".format(SPOTIFY_API_URL, 'search')


# https://developer.spotify.com/web-api/search-item/
def search(search_type, name):
    if search_type not in ['artist', 'track', 'album', 'playlist']:
        print('invalid type')
        return None
    myparams = {'type': search_type}
    myparams['q'] = name
    resp = requests.get(SEARCH_ENDPOINT, params=myparams)
    return resp.json()

# ------------------ 4. USER RELATED REQUETS  ---------- #


# spotify endpoints
USER_PROFILE_ENDPOINT = "{}/{}".format(SPOTIFY_API_URL, 'me')
USER_PLAYLISTS_ENDPOINT = "{}/{}".format(USER_PROFILE_ENDPOINT, 'playlists')
USER_TOP_ARTISTS_AND_TRACKS_ENDPOINT = "{}/{}".format(
    USER_PROFILE_ENDPOINT, 'top')  # /<type>
USER_RECENTLY_PLAYED_ENDPOINT = "{}/{}/{}".format(USER_PROFILE_ENDPOINT,
                                                  'player', 'recently-played')
BROWSE_FEATURED_PLAYLISTS = "{}/{}/{}".format(SPOTIFY_API_URL, 'browse',
                                              'featured-playlists')


# https://developer.spotify.com/web-api/get-users-profile/
def get_users_profile(auth_header):
    url = USER_PROFILE_ENDPOINT
    resp = requests.get(url, headers=auth_header)
    return resp.json()


# https://developer.spotify.com/web-api/get-a-list-of-current-users-playlists/
def get_users_playlists(auth_header):
    url = USER_PLAYLISTS_ENDPOINT
    resp = requests.get(url, headers=auth_header)
    return resp.json()


# https://developer.spotify.com/web-api/get-users-top-artists-and-tracks/
# l z. Zt. auf 50 limitiert
# Betrachtungszeitraum kann auch gesetzt werden
def get_users_top(auth_header, t, l):
    if t not in ['artists', 'tracks']:
        print('invalid type')
        return None
    url = "{}/{type}?limit={limit}".format(USER_TOP_ARTISTS_AND_TRACKS_ENDPOINT, type=t, limit=l)
    resp = requests.get(url, headers=auth_header)
    return resp.json()

# https://developer.spotify.com/web-api/web-api-personalization-endpoints/get-recently-played/
def get_users_recently_played(auth_header):
    url = USER_RECENTLY_PLAYED_ENDPOINT
    resp = requests.get(url, headers=auth_header)
    return resp.json()

# https://developer.spotify.com/web-api/get-list-featured-playlists/
def get_featured_playlists(auth_header):
    url = BROWSE_FEATURED_PLAYLISTS
    resp = requests.get(url, headers=auth_header)
    return resp.json()


# ---------------- 5. ALBUMS ------------------------
# https://developer.spotify.com/web-api/album-endpoints/

GET_ALBUM_ENDPOINT = "{}/{}".format(SPOTIFY_API_URL, 'albums')  # /<id>

# https://developer.spotify.com/web-api/get-album/
def get_album(album_id):
    url = "{}/{id}".format(GET_ALBUM_ENDPOINT, id=album_id)
    resp = requests.get(url)
    return resp.json()

# https://developer.spotify.com/web-api/get-several-albums/
def get_several_albums(list_of_ids):
    url = "{}/?ids={ids}".format(GET_ALBUM_ENDPOINT, ids=','.join(list_of_ids))
    resp = requests.get(url)
    return resp.json()

# https://developer.spotify.com/web-api/get-albums-tracks/
def get_albums_tracks(album_id):
    url = "{}/{id}/tracks".format(GET_ALBUM_ENDPOINT, id=album_id)
    resp = requests.get(url)
    return resp.json()

# ------------------ 6. USERS ---------------------------
# https://developer.spotify.com/web-api/user-profile-endpoints/

GET_USER_ENDPOINT = '{}/{}'.format(SPOTIFY_API_URL, 'users')

# https://developer.spotify.com/web-api/get-users-profile/
def get_user_profile(user_id):
    url = "{}/{id}".format(GET_USER_ENDPOINT, id=user_id)
    resp = requests.get(url)
    return resp.json()

# ---------------- 7. TRACKS ------------------------
# https://developer.spotify.com/web-api/track-endpoints/

GET_TRACK_ENDPOINT = "{}/{}".format(SPOTIFY_API_URL, 'tracks')  # /<id>
GET_AUDIO_FEATURES_ENDPOINT = "{}/{}".format(SPOTIFY_API_URL, 'audio-features')  # /<id>

# https://developer.spotify.com/web-api/get-track/
##
    
def get_track_features(auth_header, track_id):
    url = "{}/{id}".format(GET_AUDIO_FEATURES_ENDPOINT, id=track_id)
    resp = requests.get(url, headers=auth_header)
    return resp.json()

# https://developer.spotify.com/web-api/get-several-audio-features/
##

def get_several_track_features(auth_header, track_id_list):
    url = "{}/?ids={idlist}".format(GET_AUDIO_FEATURES_ENDPOINT, idlist = track_id_list)
    resp = requests.get(url, headers=auth_header)
    return resp.json()
    
# ---------------- 8. BROWSE ------------------------
# https://developer.spotify.com/web-api/browse-endpoints/
##

GET_SEEDS_ENDPOINT = "{}/{}".format(SPOTIFY_API_URL, 'recommendations/available-genre-seeds')
GET_RECOMM_ENDPOINT = "{}/{}".format(SPOTIFY_API_URL, 'recommendations')  # 


def get_recommendation_seeds_genres(auth_header):
    url = "{}".format(GET_SEEDS_ENDPOINT)
    resp = requests.get(url, headers=auth_header)
    return resp.json()

# https://developer.spotify.com/web-api/get-recommendations/
##

def get_recommendations(auth_header, query):
    url = "{}?{}".format(GET_RECOMM_ENDPOINT, query)
    resp = requests.get(url, headers=auth_header)
    return resp.json()

    