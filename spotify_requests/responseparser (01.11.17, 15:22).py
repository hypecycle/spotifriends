import string
#import random
from spotify_requests import spotify
import logging

logging.basicConfig(
    filename="spotifriends.log",
    level=logging.INFO,
    format="%(asctime)s:%(levelname)s:%(message)s"
    )

#Blueprint dict constructor
#{'FRIENDLISTKEYWORD': {'SPOTIFYUID': {'displayname': 'DISPLAYNAME', 'password': 'NONE', 'token': '16DIGITRANDOMPWD' 'exturl': 'EXTERNPROFILEURL', 'imageurl': 'IMAGEURL', tracks': [{'trackname': 'TRACKNAME', 'trackid': 'TRACKID, 'trackurl': 'TRACKEXTERNALURL', 'trackartist': 'TRACKARTIST', 'trackalbum': 'TRACKNAME', 'trackpopularity': 'TRACKNAME'}, {...}]}, 'lovely': {'displayname': 'Maria Garcia', 'url': 'http://www.mg.es', 'tracks': [{'name': '3', 'id' : 'm'}, {'name': 'e', 'id': 'b'}]}}}


def parse_users_profile(pdata):
	"""expects the user data returned from spotify. Returns a dict with relevant user data and an str with the uid
	"""

	parsed ={}	
	uid = pdata.get('id')	
	#ACHTUNG: bei leeren Images gibt es probleme. Auskommentiert: alter Version
	#parsed.update({uid: {'display_name': pdata.get('display_name'), 'password': None, 'exturl': pdata.get('external_urls', {}).get('spotify'), 'token': generate_pwd(), 'imageurl': pdata.get('images', {})[0].get('url') }})
	parsed.update({'display_name': pdata.get('display_name'), 'password': None, 'exturl': pdata.get('external_urls', {}).get('spotify'), 'token': None})	
	
	#Avoid error if picture url is empty
	if not pdata.get('images'):
		parsed.update({'imageurl': '/static/imgs/placeholder.jpg'})
	else:
		parsed.update({'imageurl': pdata.get('images', {})[0].get('url')})
	
	return parsed, uid

	
#mistet die Top Tracks aus	
def parse_users_top(tracklist):

	tracks = tracklist["items"]
	parsed = [] # empty dict
	
	for rows in tracks:
		parse_row = {}	
		parse_row.update({'trackname': rows.get('name'), 'trackid': rows.get('id'), 'trackurl': rows.get('external_urls', {}).get('spotify'), 'trackartist': rows.get('artists', {})[0].get('name'), 'artistid': rows.get('artists', {})[0].get('id'), 'trackalbum': rows.get('album', {}).get('name'), 'trackpopularity': rows.get('popularity')})
		
		parsed.append(parse_row)
	
	return parsed
	
#unused	
def complete_track_info(tracklist):
	
	for rows in tracklist['tracks']:
		track_features = spotify.get_track(rows.get('track-id'))
	
	return track_features

#unused	
def parse_track_features(track_features, track_artist_features):
	parsed = {}	
	parsed.update({'danceability': track_features.get('danceability'), 'energy': track_features.get('energy'), 'loudness': track_features.get('loudness'), 'speechiness': track_features.get('speechiness'), 'acousticness': track_features.get('acousticness'), 'instrumentalness': track_features.get('instrumentalness'), 'liveness': track_features.get('liveness'), 'valence': track_features.get('valence'), 'tempo': track_features.get('tempo')})	
	return parsed
	

#merges and returns parsed list 
def merge_several_tracks_artists(track_list, artist_list, top_track_list):

	"""merges and returns parsed list from top tracks, a reduced version from track features, and parsed artist info"""

	merged = []

	if len(track_list) == len(artist_list):
		for i in range(0, len(artist_list)):
			condensed_track_list = {}
			condensed_track_list.update(top_track_list[i])
			condensed_track_list.update({'danceability': track_list[i].get('danceability'), 'energy': track_list[i].get('energy'),'loudness': track_list[i].get('loudness'),'speechiness': track_list[i].get('speechiness'),'acousticness': track_list[i].get('acousticness'),'instrumentalness': track_list[i].get('instrumentalness'), 'liveness': track_list[i].get('liveness'), 'valence': track_list[i].get('valence'), 'tempo': track_list[i].get('tempo')})
			condensed_track_list.update(artist_list[i])
			merged.append(condensed_track_list)
	else:
		merged = ('Error: len track list: {}, len artist list: {}'.format(len(track_list), len(artist_list)))
        
	return merged
	
	
def get_artist_list_slow(auth_header, top_track_dict):

	"""expects the auth header and a dict with track infos (looks for key 'artistid'. Returns a list with genres: [list of genres]"""
	
	track_artist_features = []
	for track_to_complete in top_track_dict:
		track_artist_response = spotify.track_artist_features(auth_header, track_to_complete.get('artistid'))
		track_artist_features.append({'artistid': track_to_complete.get('artistid'), 'genres': track_artist_response.get('genres')})
	return track_artist_features

	

def build_track_list(top_track_dict):	
	"""Expects a dictionary with Tracks. Returns a list of Track IDs to submit to spotify. Endpoint 'Several Tracks' is limited to 100. No max handling, yet
	"""
	track_list = '' #list of trackid to retrieve track features 
        
	#get ids for users top tracks, build string      
	for track_to_complete in top_track_dict:
		track_list += (track_to_complete.get('trackid')) + ','
    
	return track_list

#initiates database with new friendlists	
def build_database(friendlist_name, friendListDescr, uid, profile_dict, tracks_n_artists):

	"""inititates the database. expects the Name of the friendlist [str], a description of the friend list [str], the uid [str], the profile data [str] and artists and tracks [tracks] """
	
	database = []
	entry = {}

    #eigentlich möchte man dem dictionary profile_dict den key ['tracks'] und die Liste
	#tracks_n_artists als value übergeben. Tricky: profile_dict kommt schon verschachtelt an
	#Deshalb sucht [next(iter(profile_dict))] den ersten key heraus, dann erst werden
	#key und value angebammelt. Is doch ganz einfach
	profile_dict['tracks'] = tracks_n_artists 

	entry[friendlist_name] = {}
	entry[friendlist_name]['description'] = friendListDescr
	entry[friendlist_name][uid] ={}
	entry[friendlist_name][uid].update(profile_dict)
	
	database.append(entry)
	
	return database
	
	
def init_database(auth_header, friendList, friendListDescr):
	"""Does the heavy lifting. Expects the auth header, the friend list name, description. Calls all requests and parsers
	"""
	profile_data = spotify.get_users_profile(auth_header)
	profile_dict, uid = parse_users_profile(profile_data)
	logging.info("Profile data retrieved for {}".format(uid))

	user_top_tracks = spotify.get_users_top(auth_header, "tracks", 50)  
	top_track_dict = parse_users_top(user_top_tracks)
	logging.info("{} Top tracks retrieved and parsed".format(len(user_top_tracks)))
	
	several_track_features = spotify.get_several_track_features(auth_header, build_track_list(top_track_dict)) 
	logging.info("{} tracks' features returned from spotify".format(len(several_track_features)))
	
	track_artist_features = get_artist_list_slow(auth_header, top_track_dict)
	logging.info("Track artist features retrieved")

	
	merged_tracklist = merge_several_tracks_artists(several_track_features.get('audio_features'), track_artist_features, top_track_dict)
	database = build_database(friendList, friendListDescr, uid, profile_dict, merged_tracklist)


	return database




