import logging
import datetime
import pickle
import string
import random
from spotify_requests import responseparser
from spotify_requests import spotify


logging.basicConfig(
    filename="spotifriends.log",
    level=logging.INFO,
    format="%(asctime)s:%(levelname)s:%(message)s"
    )


def generate_pwd(size=32, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))
	

def render_list_of_friendlists(uid):

    """ Provides the overview in the profile page. Expects the database sorted by friendlists.
     Scheme: [{friendlist: [{dict of user}, {dict of user}], 'description':
    Returns a list of friendlists withe items relevant for the user"""
    
    friendlist_database = load_update_friendlist_database('database_friendlist')

    friendlist_membership = {'HOST': [], 'INVITED': [], 'JOINED': [], 'REJECTED': []} #scheme for db, adding entries

    for h in ('HOST', 'INVITED', 'JOINED', 'REJECTED'): #iterating through status

        for i in friendlist_database: #iterating through all friendlists
            friendlist_itername = (next(iter(i))) # returns the friendlist names of friendlist_database
            joined, invited, host = 0,0,0
            
            #lets count:
            #a little clumsy
            if len(i[friendlist_itername]) > 0:
                for k in range(len(i[friendlist_itername])):
                    if i[friendlist_itername][k].get('status') == "INVITED": 
                        invited = invited + 1 #counting invites of actual friendlist
                    if i[friendlist_itername][k].get('status') == "JOINED": 
                        joined = joined + 1 #counting invites of actual friendlist
                    if i[friendlist_itername][k].get('status') == "HOST": 
                        host = host + 1
                    
                    if joined == 1: 
                        friend_grammar = 'friend'
                    else:
                        friend_grammar = 'friends'             

            for j in i.get(friendlist_itername): #iterates through all entries in the user list         

                if j.get('user') == uid and h == j.get('status'): #if the right user and the right status is in the list …
                    friendlist_membership[h].append({'friendlist': friendlist_itername, 'description': i.get('description'), 'INVITED': invited, 'JOINED': joined + host, 'HOST': host, 'TOTAL': host + joined + invited, 'friend_grammar': friend_grammar})

    return(friendlist_membership)
    

# old style, if not in use, delete     
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
        #logging.info('File name: {}, database {}'.format(fileName, database))

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
    
    
# old style, deprecated, delete?
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
    

def invite_by_token(token, uid):

    """Is called, when user is invited by token.  Expects the token and uid. Loads and saves db.
    If UID is none it just returns the error and doesn't change the db.
    If UID is set, it changes db values. Checks that status is INVITED and changes to JOINED. Thus, once the link is found 
    and changed, the link becomes invalid."""

    error = True

    friendlist_database = load_update_friendlist_database('database_friendlist')

    for i in range(len(friendlist_database)): #iterating through lists in friendlists 
        friendlist_itername = (next(iter(friendlist_database[i]))) # returns the friendlist names of friendlist_database
           
        for j in range(len(friendlist_database[i][friendlist_itername])):
            #print(friendlist_database[i][friendlist_itername][j])
            if friendlist_database[i][friendlist_itername][j].get('token') == token and friendlist_database[i][friendlist_itername][j].get('status') == 'INVITED':
                if uid:
                    friendlist_database[i][friendlist_itername][j]['user'] = uid
                    friendlist_database[i][friendlist_itername][j]['status'] = 'JOINED'
                error = False
                break

    logging.info('friendlisparser: Token {} and uid {} produce error={}'.format(token, uid, error))
    save_friendlist_database(friendlist_database, 'database_friendlist')

    return error
        
          
def check_friendlist(searchterm):

    """Expects a friendlist name to check. Returns True if already taken"""
    
    friendlist_database = load_update_friendlist_database('database_friendlist')
    check = False
    
    for friendlist_item in friendlist_database:
        if searchterm in friendlist_item:
            check = True
            logging.info('New friendlist: {} already taken'.format(searchterm))
            
    return check


def create_friendlist(friendlist_name, friendlist_description, givenname_invited, mail_invited, host_uid):

    """adds friendlist, host and a first friend to the friendlist
    Creates list of dicts for host (‚status‘ = ‚HOST‘) and first user 
    (‚status‘ = ‚INVITED‘). Adds them to the database_friendlist."""
    
    friendlist_database = load_update_friendlist_database('database_friendlist')
    
    #initiates host
    friendlist_userlist = [{'user': host_uid, 'givenname': None, 'invite_mail': None, 'status': 'HOST', 'token': None}]
    
    #Adds users to invite
    friendlist_userlist.append({'user': None, 'givenname': givenname_invited, 'invite_mail': mail_invited, 'status': 'INVITED', 'token': generate_pwd()})
    
    friendlist_builder = {friendlist_name: friendlist_userlist, 'description': friendlist_description, 'genres': {}, 'clusters': {}}
    friendlist_database.append(friendlist_builder)
    
    save_friendlist_database(friendlist_database, 'database_friendlist')

    return 

def ask_friendlist(friendlist_name, uid):
    """expects the friendlist_name, return a list of users already in + the description """

    friendlist_database = load_update_friendlist_database('database_friendlist')

    friends_to_edit = []
    
    for friendlist in friendlist_database: #iterating friendlist_databse into single friendlists
        friendlist_itername = (next(iter(friendlist))) # returns the name of the current friendlist

        if friendlist_name in friendlist:
            description_to_edit = friendlist.get('description')
            for friend in friendlist.get(friendlist_itername): #gets each friend in the friendlist
                if friend.get('user') != uid: #add everybody except the host
                    friends_to_edit.append(friend)
                
    return friends_to_edit, description_to_edit
    
def add_friend(friendlist_name, givenname_invited, mail_invited):
    """takes friendlist name, a givenname, a mail and creates a new friend for this user, the saves the updated list """

    friendlist_database = load_update_friendlist_database('database_friendlist')

    friend_builder = {'user': None, 'givenname': givenname_invited, 'invite_mail': mail_invited, 'status': 'INVITED', 'token': generate_pwd()}
   
    for i in range (0, len(friendlist_database)): #iterating friendlist_databse into single friendlists
        friendlist_itername = (next(iter(friendlist_database[i]))) # returns the name of the current friendlist

        if friendlist_name in friendlist_database[i]:
            friendlist_database[i][friendlist_itername].append(friend_builder)

    save_friendlist_database(friendlist_database, 'database_friendlist')           

    return
    
def get_token(friendlist_name, mail_invited):

    friendlist_database = load_update_friendlist_database('database_friendlist')
    
    for friendlist in friendlist_database:
        if friendlist_name in friendlist:
            for friend in friendlist.get(friendlist_name):
                if mail_invited == friend.get('invite_mail'):
                    token = friend.get('token')
                    break
                    
    return token
                    
#nowhere called, yet!                    
def create_playlist(auth_header, uid, friendlist_name, friendlist_descr):
        
        """Builds the playlist in the current user's account. Expects auth-header, uid,
        friendlist_name = playlist_name, friendlist_descr = playlist_descr
        Receives playlist-info and saves it to 
        [{friendlist: {'user': UID, 'snapshot': playlist_sh, 'href': url, 
        'id': id,}
        Test: frl_db[4].get('Where the streets have no name')[0].get('user') works
        !!!!!Make sure that it is called just once (after accepted invite) !!! Or check if id is already present and chose update!!!!
        """

        name = friendlist_name
        description = friendlist_descr
        collaborative = 'false' #small caps
        public = 'false'
        
        friendlist_database = load_update_friendlist_database('database_friendlist')
        
        query = "{\"name\":\"" + name + "\", \"description\":\"" + description + "\", \"collaborative\":" + collaborative + ", \"public\":" + public + "}"
        
        uid = '1121800629'
                
        status, response = spotify.create_playlist(auth_header, uid, query)
        
        1/0
        
        if status == 200 or status == 201: #bueno
        
            for i in range (0, len(friendlist_database)): #iterating through lists in friendlist_databse 
                friendlist_itername = (next(iter(friendlist_database[i]))) # returns  name the current friendlist
                
                if friendlist_name in friendlist_database[i]:
                    friendlist_content = friendlist_database[i].get(friendlist_name)
                    
                    for j in range(len(friendlist_content)):
                        if friendlist_content[j].get('user') == uid: #check if already created "and not friendlist_database[i].get(friendlist_itername)[j].get('playlist_id'):" 
                            friendlist_database[i][friendlist_itername][j]['snapshot_id'] = response.get('snapshot_id')
                            friendlist_database[i][friendlist_itername][j]['playlist_url'] = response.get('external_urls').get('spotify')
                            friendlist_database[i][friendlist_itername][j]['playlist_id'] = response.get('id')
                            logging.info('friendlisparser: Playlist {} for {} created. Snapshot {}, id {}, status {}'.format(friendlist_name, uid, response.get('snapshot_id'), response.get('id'), status))
                        else:
                            logging.info('friendlisparser ERROR: Updating playlist db {} for {} failed.'.format(friendlist_name, uid))
                        

        else:
            logging.info('friendlisparser ERROR: Creating playlist {} for {} failed. status {}'.format(friendlist_name, uid, status))
                
        save_friendlist_database(friendlist_database, 'database_friendlist')           
        
        return