import string
#import random
from spotify_requests import spotify, friendlistparser
import logging
import datetime
import pickle

logging.basicConfig(
    filename="spotifriends.log",
    level=logging.INFO,
    format="%(asctime)s:%(levelname)s:%(message)s"
    )


def parse_users_profile(pdata):
    """expects the user data returned from spotify. Returns a dict with relevant user data and an str with the uid
    """

    parsed ={}    
    uid = pdata.get('id')    
    #ACHTUNG: bei leeren Images gibt es probleme. Auskommentiert: alter Version
    #parsed.update({uid: {'display_name': pdata.get('display_name'), 'password': None, 'exturl': pdata.get('external_urls', {}).get('spotify'), 'token': generate_pwd(), 'imageurl': pdata.get('images', {})[0].get('url') }})
    
    parsed.update({'display_name': pdata.get('display_name'), 'password': None, 'givenname': None, 'exturl': pdata.get('external_urls', {}).get('spotify')})    
    
    #Avoid error if picture url is empty
    if not pdata.get('images'):
        parsed.update({'imageurl': '/static/imgs/placeholder.jpg'})
    else:
        parsed.update({'imageurl': pdata.get('images', {})[0].get('url')})
        
    #Fill empty name with useful Info
    #1. display_name, 2. given_name, 3. uid
    cumulated_temp = uid
    
    if pdata.get('given_name'):
        cumulated_temp = pdata.get('given_name')
    elif pdata.get('display_name'):
        cumulated_temp = pdata.get('display_name')
        
    parsed.update({'cumulated_name': cumulated_temp})    
        
    #add Lat login timestamp
    lastLogin = ('{:%Y%m%d%H%M%S}'.format(datetime.datetime.now()))
    parsed.update({'login': lastLogin})
    
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
        merged = [] # inconsistent cases return an empty database
        
    return merged
    
    
def get_artist_list_slow(auth_header, top_track_dict):

    """expects the auth header and a dict with track infos (looks for key 'artistid'. Returns a list with genres: [list of genres]"""

    logging.info('Starting to get artist features')
    
    track_artist_features = []
    for track_to_complete in top_track_dict:
        track_artist_response = spotify.track_artist_features(auth_header, track_to_complete.get('artistid'))
        track_artist_features.append({'artistid': track_to_complete.get('artistid'), 'genres': track_artist_response.get('genres')})
        
    logging.info('Getting artist features finished')

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
def format_uid_entry(uid, profile_dict, tracks_n_artists):

    """inititates the database old style with friendlist as key. expects the Name of the friendlist [str], a description of the friend list [str], the uid [str], the profile data [str] and artists and tracks [tracks] """
    
    database = []
    entry = {}

    #eigentlich möchte man dem dictionary profile_dict den key ['tracks'] und die Liste
    #tracks_n_artists als value übergeben. Tricky: profile_dict kommt schon verschachtelt an
    #Deshalb sucht [next(iter(profile_dict))] den ersten key heraus, dann erst werden
    #key und value angebammelt. Is doch ganz einfach
    profile_dict['tracks'] = tracks_n_artists 

    entry[uid] ={}
    entry[uid].update(profile_dict)
    
    database.append(entry)
    
    return database
    
    
def get_user_data(auth_header, profile_data):
    """Does the heavy lifting. Expects the auth header, the friend list name, description. Calls all requests and parsers
    """
    profile_dict, uid = parse_users_profile(profile_data) # returns dict with display name etc.
    logging.info("Profile data retrieved for {}".format(uid))

    user_top_tracks = spotify.get_users_top(auth_header, "tracks", 50) # get user's top tracks.
    top_track_dict = parse_users_top(user_top_tracks)
    logging.info("{} Top tracks retrieved and parsed".format(len(user_top_tracks)))
    
    several_track_features = spotify.get_several_track_features(auth_header, build_track_list(top_track_dict)) 
    logging.info("{} tracks' features returned from spotify".format(len(several_track_features)))
    
    track_artist_features = get_artist_list_slow(auth_header, top_track_dict)
    logging.info("Track artist features retrieved")

    
    merged_tracklist = merge_several_tracks_artists(several_track_features.get('audio_features'), track_artist_features, top_track_dict)
    database = format_uid_entry(uid, profile_dict, merged_tracklist)


    return database, uid

def load_database(fileName):

    """ Loads databases from data-folder, returns unpickled list """
    
    logging.info("*** start responseparser.load_database()")

    try:
        with open('data/' + fileName+'.pickle', 'rb') as handle:
            data = pickle.load(handle)
    except:
        logging.info("responseparser.load_database(): Loading failed")
        data = []
    
    logging.info("*** finished responseparser.load_database()")
    return data
    
    
def save_database(fileName, database):

    """ Writes databases as pickled file """
    
    logging.info("*** start responseparser.save_database()")

    
    try:
        with open('data/' + fileName+'.pickle', 'wb') as handle:
            pickle.dump(database, handle, protocol=pickle.HIGHEST_PROTOCOL)
    except:
        logging.info("responseparser.save_database(): Saving failed")
        
    logging.info("*** finished responseparser.save_database()")

    return 
 

def update_main_user_db(database_current_user):

    """ Loads database 'database_user'. Does all the magic. If database_user is empty or uid not present: 
    appends database_current_user. If user present: Updates info in database. Two methods in test_dict9 on MacBook
    friend_list is needed for auto_invite until real invite is set. returns the updated
    db and a change flag True."""
    
    #loads database up to now. Passes to var
    database_user_before = load_database('database_user') 
    
    #basis for building new database. Adding existing item or current user item 
    database_user_new = [] 
    
    #Gets toggled, when the user-uid was found and current user added. 
    known_user = False 
    
    #Remains false, when key not found due to empty database or new user
    
    for i in database_user_before:
    
        #iteration uid equals current user uid
        if next (iter (i)) == next (iter (database_current_user[0])): 
        
            #add current user at the place of the old info
            database_user_new.append(database_current_user[0])        
              
            known_user = True #changed!
            logging.info("Found user {}".format(next (iter (database_current_user[0]))))
        else:
            database_user_new.append(i) #iteration uid not user? add old item
            #logging.info("User {} (before) and user {} (current) don't match".format(next(iter(i)), next (iter (database_current_user[0]))))

    
    #if the search term hasn't been found, add user at the end   
    if not known_user:
        database_user_new.append(database_current_user[0])
        logging.info("User {} not found updating user db. Appended".format(next (iter (database_current_user[0]))))

        '''###find clever way to pass auto-invite        
        friendlistparser.auto_invite(database_current_user[0]) #calls friendlist-function that updates and saves the db'''
        
    save_database('database_user', database_user_new)
    
    return database_user_new, known_user
    

#OLD METHOD: current user is not present in the new structure 23.11.
#Still called from dashboard
def parse_name(current_user):
    """Parse current user to return the name. 1. display_name, 2. given_name, 3. uid"""
    
    user_data = current_user[0].get(next(iter(current_user[0]))).get('cumulated_name')
    
    return user_data #return UID

#New method: parses profile_data
def parse_name_pd(profile_data):
    """Parse current user to return the name. 1. display_name, 2. uid"""
    
    user_data = profile_data.get('display_name')
    
    if not user_data:
        user_data = profile_data.get('id')
    
    return user_data 
    
#OLD METHOD: current user is not present in the new structure 23.11.    
def parse_image(current_user):
    """Parse current users dataset to return image_url. Alternative URL for users with no image has been constructed earlier in parse_users_profile"""
    
    user_data = current_user[0].get(next(iter(current_user[0])))
    
    return user_data.get('imageurl')

#New method: parses profile_data
def parse_image_pd(profile_data):
    """Parse current users dataset to return image_url. Alternative URL for users with no image is set"""
    
    if profile_data.get('images'):    
        user_data = profile_data.get('images')[0].get('url')
    else:
        user_data = '/static/imgs/placeholder.jpg'
    
    return user_data
    
def parse_user_list_dashboard(user_database):
    """parse and return a list of strings with users and data ready for dashboard"""

    user_list = []
    
    for i in user_database:
        user_list.append("Name: {}, last login: {}".format(i.get(next(iter(i))).get('cumulated_name'), i.get(next(iter(i))).get('login')))

    
    return user_list
        
    
