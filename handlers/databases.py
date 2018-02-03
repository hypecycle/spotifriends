import string
#import random
from spotify_requests import spotify, friendlistparser, genreparser
import logging
from datetime import datetime
import pickle

logging.basicConfig(
    filename="spotifriends.log",
    level=logging.INFO,
    format="%(asctime)s:%(levelname)s:%(message)s"
    )

FALLBACK_IMAGE_PATH = '/static/imgs/placeholder.jpg'


def load_database(fileName):

    """ Loads databases from data-folder, returns unpickled list """
    

    try:
        with open('data/' + fileName+'.pickle', 'rb') as handle:
            data = pickle.load(handle)
    except:
        logging.info("databases: loading database {} FAILED".format(fileName))
        data = []
    
    logging.info("databases: loaded database {}".format(fileName))
    return data
    
    
def save_database(fileName, database):

    """ Writes databases as pickled file """
    
    try:
        with open('data/' + fileName+'.pickle', 'wb') as handle:
            pickle.dump(database, handle, protocol=pickle.HIGHEST_PROTOCOL)
    except:
        logging.info("databases: saving database {} FAILED".format(fileName))
        
    logging.info("databases: saved database {} successfully".format(fileName))

    return 


def update_userDB(currUsrData, uid):

    """ Loads 'database_user', expects uid. 
    If database_user is empty or uid not present: 
    appends currUsrData. If user present: 
    Updates info in database. returns flag True
    if current user is known
    """
    
    #loads database up to now. Passes to var
    userDB = load_database('database_user') 
    
    #Gets toggled, when the user-uid was found and current user added. 
    known_user = False 
     
    #Remains false, when key not found due to empty database or new user    
    for i in range(len(userDB)):
    
        #iteration uid equals current user uid
        if next (iter (userDB[i])) == uid: 

            #add current user at the place of the old info
            userDB[i] = {}       
            userDB[i].update({uid: currUsrData})  
              
            known_user = True #changed!
            logging.info("databases: Found user {}. Replaced".format(uid))

    
    #if the search term hasn't been found, add user at the end   
    if not known_user:
        userDB.append({uid:currUsrData})
        logging.info("databases: User {} not found. database_user updated.".format(uid))
    

    save_database('database_user', userDB)
    
    return known_user



def buildUsrData(profileData, currUsrTracks):
    """Expects the profile data returned from spotify
    and the tracks. Returns a dataset completely
    formatted with cumulated_name, image info, tracks
    Login-Info 
    """

    builder = {}    
    uid = profileData.get('id')    
   
    builder.update({'display_name': profileData.get('display_name'), 
                    'password': None, 'givenname': None, 
                    'exturl': profileData.get('external_urls').get('spotify')})    
    
    #Avoid error if picture url is empty
    if not profileData.get('images'):
        builder.update({'imageurl': FALLBACK_IMAGE_PATH})
    else:
        builder.update({'imageurl': profileData.get('images')[0].get('url')})

    builder.update({'tracks': currUsrTracks})
        
    #Fill empty name with useful Info
    #1. display_name, 2. given_name, 3. uid
    cumulated_temp = uid
    
    if profileData.get('given_name'):
        cumulated_temp = profileData.get('given_name')
    elif profileData.get('display_name'):
        cumulated_temp = profileData.get('display_name')
        
    builder.update({'cumulated_name': cumulated_temp})    
        
    #add Lat login timestamp
    lastLogin = ('{:%Y%m%d%H%M%S}'.format(datetime.now()))
    builder.update({'login': lastLogin})
    
    return builder


def fetchData(uid):
    """
    Loads databases and check if uid is database. If user not in db or
    user is in db and last login is older than a day, returns true
    and forces function in app/callback to load data and update the db.
    Otherwise just shortcuts to profile
    """

    userDB = load_database('database_user') 
    reloadFlag = True

    for i in range(len(userDB)):
    
        #iteration uid equals current user uid
        if next (iter (userDB[i])) == uid: 
            lastLoginStr = userDB[i].get(uid).get('login')
            last = datetime.strptime(lastLoginStr, '%Y%m%d%H%M%S') 
            now = datetime.now()
            delta = now -last
            if delta.days < 1:
                reloadFlag = False

            logging.info("databases: User {} login {} days ago. Db updated: {}.".format(uid, delta.days, reloadFlag))

    return reloadFlag





