import logging
import datetime
import pickle
import string
import random
from spotify_requests import responseparser


logging.basicConfig(
    filename="spotifriends.log",
    level=logging.INFO,
    format="%(asctime)s:%(levelname)s:%(message)s"
    )


def generate_pwd(size=32, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))
	

def render_list_of_friendlists(friendlist_database, uid):

    """Expects the database sorted by friendlists. Scheme: [{friendlist: [{dict of user}, {dict of user}], 'description':"""

    friendlist_membership = {'HOST': [], 'INVITED': [], 'JOINED': [], 'REJECTED': []} #scheme for db, adding entries

    for h in ('HOST', 'INVITED', 'JOINED', 'REJECTED'): #iterating through status
        for i in friendlist_database: #iterating through all friendlists
            friendlist_itername = (next(iter(i))) # returns the friendlist names of friendlist_database

            invited, joined = 0,0

            for j in i.get(friendlist_itername): #iterates through all entries in the user list

                if j.get('status') == "INVITED": invited =+1 #counting invites of actual friendlist
                if j.get('status') == "JOINED" or j.get('status') == "HOST": joined =+1
                
                if invited + joined == 1: 
                    friend_grammar = 'friend'
                else:
                    friend_grammar = 'friends'

                if j.get('user') == uid and h == j.get('status'): #if the right user and the right status is in the list …
                    friendlist_membership[h].append({'friendlist': friendlist_itername, 'description': i.get('description'), 'invited': invited + joined, 'joined': joined, 'friend_grammar': friend_grammar})

    return(friendlist_membership)
    
    
def update_friendlist(friendlist_database, friendlist_to_join, uid, new_status):

    """Expects friendlist_database, the name of the friendlist to join, uid and the new status"""

    friendlist_builder = []  #blueprint
    friendlist_feature_builder = {} #blueprint

    for friendlist_list_object in friendlist_database: #iterating through all friendlists 
        friendlist_itername = (next(iter(friendlist_list_object))) # returns the friendlist names of friendlist_database

        friendlist_user_builder = {friendlist_itername: []} #blueprint      

        for j in friendlist_list_object.get(friendlist_itername): #pick actual friendlist
            if j.get('user') == uid and friendlist_itername == friendlist_to_join:
                j['status'] = new_status

            friendlist_user_builder[friendlist_itername].append(j)

        for key in friendlist_list_object: #get key/val-Pairs
            if key != friendlist_itername: #Friendlist-name as a dict key is treated diiferently 
                friendlist_feature_builder[key] = friendlist_list_object.get(key) #key/val
                
            friendlist_user_builder.update(friendlist_feature_builder)

        friendlist_builder.append(friendlist_user_builder)

    return(friendlist_builder)
    
    
    
    
def load_update_friendlist_database(fileName):

    """ Loads databases from data-folder, returns unpickled list """
    
    try:
        with open('data/' + fileName+'.pickle', 'rb') as handle:
            data = pickle.load(handle)
    except:
        logging.info("Loading friendList failed.")
        data = [{'17hours2hamburg': [],'description': 'The longer the way, the better the playlist', 'genres': {}, 'clusters': {}},{'The_end_is_near': [],'description': 'Worlds last best party', 'genres': {}, 'clusters': {}}, {'Lapdance_night': [],'description': 'Lap to lap', 'genres': {}, 'clusters': {}},{'Partyaninamlparty': [], 'description': 'Calling all animals', 'genres': {}, 'clusters': {}}]

    return data



def save_friendlist_database(database, fileName):

    """ Writes databases as pickled file. Expects database, fileName """

    try:
        with open('data/' + fileName+'.pickle', 'wb') as handle:
            pickle.dump(database, handle, protocol=pickle.HIGHEST_PROTOCOL)
        logging.info("Friendlist saved")
        logging.info('File name: {}, database {}'.format(fileName, database))

    except:
        logging.info("Saving friendlist failed")
        #logging.info('File name: {}, database {}'.format(fileName, database))
    return
    
    
    
def auto_invite(uid):

    """Helper/dummy function: loads db, invites and auto-joins users to a friendlist, 
    saves db and returns the new friendlist"""


    logging.info("Entered auto-invite")

    friendlist_database = load_update_friendlist_database('database_friendlist')
    

    friendlist_builder = []  #blueprint
    friendlist_feature_builder = {} #blueprint
    friendlist_database_builder = []


    for friendlist_list_object in friendlist_database:
        
        friendlist_itername = (next(iter(friendlist_list_object)))
        friendlist_user_builder = []

        i = friendlist_list_object.get(friendlist_itername)
        
        #Give different status messages to different friendlists
        status_builder = "JOINED" 
        
        if friendlist_itername == '17hours2hamburg':
            status_builder = 'REJECTED'
        elif friendlist_itername == 'The_end_is_near':
            status_builder = 'HOST'

        
        i.append({'user': uid, 'status': status_builder, 'token': generate_pwd()})

        friendlist_user_builder.append(i)

        friendlist_builder = [{friendlist_itername}] 

        friendlist_builder = {friendlist_itername: friendlist_user_builder[0]}

        for key in friendlist_list_object: #get key/val-Pairs
            if key != friendlist_itername: #Friendlist-name as a dict key is treated diiferently 
                friendlist_feature_builder[key] = friendlist_list_object.get(key) #key/val
                
            friendlist_builder.update(friendlist_feature_builder)
        
        friendlist_database_builder.append(friendlist_builder)
        
    save_friendlist_database(friendlist_database_builder, 'database_friendlist')

    return
    
    
    
def resolve_token(token):

    """Takes the friendlist and a token and returns the user, the name of the friendlist plus a boolean error"""

    friendlist_database = load_update_friendlist_database('database_friendlist')
    invited_user =  ''
    friendList = ''
    error = True

    """ccc"""
    for friendlist_item in friendlist_database:
        itername = (next(iter(friendlist_item)))
        for users in friendlist_item.get(itername):
            #print(users.get('token'))
            if users.get('token') == token:
                print('found')
                invited_user = users.get('user')
                friendList = itername
                error = False
                break

    return(invited_user, friendList, error)
        
          
def check_friendlist(searchterm):

    """Expects a friendlist name to check. Returns True if already taken"""
    
    friendlist_database = load_update_friendlist_database('database_friendlist')
    check = False
    
    for friendlist_item in friendlist_database:
        if searchterm in friendlist_item:
            check = True
            logging.info('New friendlist: {} already taken'.format(searchterm))
            
    return check


