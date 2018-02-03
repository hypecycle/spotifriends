import string
#import random
from spotify_requests import spotify, friendlistparser, genreparser
import logging
import datetime
import pickle

logging.basicConfig(
    filename="spotifriends.log",
    level=logging.INFO,
    format="%(asctime)s:%(levelname)s:%(message)s"
    )

# True to get a detailed log
PLAYLIST_DETAIL = True

def get_top_tracks(auth_header):
    """Pulls the list of the top 50 songs from spotify. The call is limited to 50 items.
    If you set offset to 49, it starts to read the list from 49 to 99 – 50 songs extra.
    Returned data is enclosed in 'items' key, so I call spotify twice and run
    parse_user_top twice. 
    """
    usrTopTracks = spotify.get_users_top(auth_header, "tracks", 50, 0)
    usrTopList = parse_user_top(usrTopTracks.get('items'))

    usrTopTracks = spotify.get_users_top(auth_header, "tracks", 50, 49)
    usrTopList += parse_user_top(usrTopTracks.get('items'))
            
    return usrTopList

    
def get_recent_tracks(auth_header):
    """Pulls the list of the recent 50 songs from spotify. The call is limited to 50 items.
    You can specify unix timestamps, but this doesn't help to get more. 
    """
    usrRecent = spotify.get_users_recently_played(auth_header, "track", 50)    
    # different format for 'items'[list] make same before call or die
    usrRecentList = parse_user_recent(usrRecent)
    
    return usrRecentList
    
def get_tracks_in_playlists(auth_header, uid):
    """Kindly asks for the total number of all playlists: playlTotal 
    Then loops over dataset in steps of 50ies until offset + limit 
    exceeds playlTotal. Then cuts down the limit to get the remaining playlists.
    Parses a list of IDs out of the returned data for every list that is not 
    'images' = []. (This is a reliable marker for playlists that don't return tracks, 
    e.g. being imported from iTunes). Then loads track info for track ID's
    """
    
    if PLAYLIST_DETAIL is True:
        logging.info("tracks: get_tracks_in_playlists entered")
    
    # -------- Getting the total number of users playlists ----------
    playlTotal = spotify.get_list_of_users_playlists(auth_header, uid, 1, 0).get('total')
    usrPlayl = []
    
    limit = 50
    offset = 0
    
    # ------------ Getting playlists as IDs -----------------
    while offset < playlTotal:
        usrPlayl += spotify.get_list_of_users_playlists(auth_header, uid, limit, offset).get('items')
        offset += limit
               
    usrPlaylIDs = parse_user_playlist_ids(usrPlayl)
    usrPlaylTrack =[]
    usrPlaylTrackFAILED = []

    if PLAYLIST_DETAIL is True:
        logging.info("tracks: {} playlists returned".format(playlTotal))
        logging.info("tracks: playlist id's: {} ".format(usrPlaylIDs))

    
    #  ----- Takes the list of IDs, loops over it and asks for tracks in each list ------
    
    for ID in usrPlaylIDs:
        trackList = spotify.get_playlist_tracks(auth_header, uid, ID).get('items')
        if trackList:
            for i in range(len(trackList)):
                trackID = trackList[i].get('track').get('id')
                if trackID:
                    usrPlaylTrack.append(trackID)
                else:
                    usrPlaylTrackFAILED.append(ID)

            if PLAYLIST_DETAIL is True:
                logging.info("tracks: {} tracks for playlist {} returned"
                             .format(len(trackList), ID))

    if PLAYLIST_DETAIL is True:
        logging.info("tracks: {} tracks received as ID".format(len(usrPlaylTrack)))
            
    
    counter = 0 
    limit = 50
    usrPlaylTrackInfo = []
    
    #  ----- Asks for info for each track and parses relevant data ------
  
    while counter < len(usrPlaylTrack):            
        if counter + limit >= len(usrPlaylTrack):
            limit = len(usrPlaylTrack) - counter
        
        trackReqStr = ''
        for i in range(counter, counter + limit):
            trackReqStr += usrPlaylTrack[i] + ','
        
        # Get rid of the last comma
        trackReqStr = trackReqStr[:-1]
        
        usrPlaylTrackInfoResp = spotify.get_several_tracks(auth_header, trackReqStr)
        usrPlaylTrackParse = parse_user_top(usrPlaylTrackInfoResp.get('tracks'))
        usrPlaylTrackInfo += usrPlaylTrackParse
        
        counter += limit
        
    if PLAYLIST_DETAIL is True:
        logging.info("tracks: Infos for all tracks received".format(len(usrPlaylTrack)))
            
    return usrPlaylTrackInfo
  
  
def parse_user_playlist_ids(playlists):
    """
    Parses all the Playlist IDs out of all the Playlists. Expects the object
    returned by spotify with a list of playlists. get's the val list associated
    with the key 'items' returns a list. 
    """
    usrPlaylIDs = []
    for playlist in playlists:
        if playlist.get('images'):
            usrPlaylIDs.append(playlist.get('id'))
        
    return usrPlaylIDs
    

def parse_user_top(tracklist):
    """ Gets a list of tracks returned from get_top_tracks with a lot of overhead
    information. Picks out relevant key/val data and stores them in a format
    that's ready for currUsrTracks. 'get_recent_tracks' and 'get_recent_top' return
    differently formatted tracks -- thus we have two parsers. 
    """

    tracks = tracklist
    parsed = [] # empty dict
    
    
    for i in range(len(tracks)):
        track = tracks[i]
        parse_tracks = {}    
        parse_tracks.update({'trackname': track.get('name'), 'trackid': track.get('id'), 
                          'trackurl': track.get('external_urls', {}).get('spotify'),
                          'trackuri': track.get('uri'),
                          'trackartist': track.get('artists', {})[0].get('name'), 
                          'artistid': track.get('artists', {})[0].get('id'), 
                          'trackalbum': track.get('album', {}).get('name'), 
                          'trackpopularity': track.get('popularity')
                          })
                                  
        parsed.append(parse_tracks)
    
    return parsed
    
def parse_user_recent(tracklist):
    """ Gets a list of tracks returned from get_recent_tracks with a lot of overhead
    information. Picks out relevant key/val data and stores them in a format
    that's ready for currUsrTracks. 'get_recent_tracks' and 'get_recent_top' return
    differently formatted tracks -- thus we have two parsers. 
    """

    tracks = tracklist["items"]
    parsed = [] # empty dict
    
    for i in range(len(tracks)):
        track = tracks[i]
        parse_tracks = {}    
        parse_tracks.update({'trackname': track.get('track').get('name'), 
                          'trackid': track.get('track').get('id'), 
                          'trackurl': track.get('track').get('external_urls').get('spotify'),
                          'trackuri': track.get('track').get('uri'),
                          'trackartist': track.get('track').get('artists')[0].get('name'), 
                          'artistid': track.get('track').get('artists')[0].get('id'), 
                          'trackalbum': track.get('track').get('album').get('name'), 
                          'trackpopularity': track.get('track').get('popularity')
                          })
        
        parsed.append(parse_tracks)
    
    return parsed

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
    appends database_current_user. If user present: Updates info in database. returns the updated
    db and a change flag True."""
    
    #loads database up to now. Passes to var
    database_user_before = load_database('database_user') 
    
    #basis for building new database. Adding existing item or current user item 
    database_user_new = [] 
    
    #Gets toggled, when the user-uid was found and current user added. 
    known_user = False 
    
    #----------- Statistics for genres, music features etc. goes here ---------------
    # database_current_user[0] contains a dict in the expected form
    # 'uid': {'display_name', name, … 'imageurl': url, tracks: [['trackname': name, ... 'genres': ['1', '2', ]
    
    #counts the genres of all tracks and adds them to the database_current_user
    #adds 'genres:{'subgenre1': occurance, ' sg2': occurances …}
    uid = next(iter(database_current_user[0]))
    
    database_current_user[0][uid]['genres'] = {}
    database_current_user[0][uid]['genres'] = (genreparser.count_genres(database_current_user[0]))
    
    #takes the genres count, compares it to the genre_db and finds the x best supergenres
    #returns a list with the key 'supergenres'
    database_current_user[0][uid]['supergenres'] = {}
    database_current_user[0][uid]['supergenres'] = genreparser.find_genre_weight(database_current_user[0], 3)
     
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
        
    save_database('database_user', database_user_new)
    
    return database_user_new, known_user
    


#New method: parses profile_data
def parse_name_pd(profile_data):
    """Parse current user to return the name. 1. display_name, 2. uid"""
    
    user_data = profile_data.get('display_name')
    
    if not user_data:
        user_data = profile_data.get('id')
    
    return user_data 
    

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
        
    
