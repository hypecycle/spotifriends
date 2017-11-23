import logging
import datetime
import pickle
from spotify_requests import responseparser


logging.basicConfig(
    filename="spotifriends.log",
    level=logging.INFO,
    format="%(asctime)s:%(levelname)s:%(message)s"
    )


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

    """Expects friendlist_database, the name of the friendlist to join, uid and the new status

    """

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
        logging.info("Loading friendList failed. inserted generic data")
        data = [{'17hours2hamburg': [{'user': '1121800629', 'status': 'HOST', 'token': '1234567890123455'}, {'user': 'anja*hh*', 'status': 'INVITED', 'token': 'RND16DTOKENJHOKN'}],'description': 'The longer the way, the better the playlist', 'genres': {}, 'clusters': {}},{'The_end_is_near': [{'user': '1121800629', 'status': 'JOINED', 'token': 'JHUNGJOKHNKGOHGS'}, {'user': 'anja*hh*', 'status': 'HOST', 'token': 'HGUJHGZTVBKLOÖMN'}],'description': 'Worlds last best party', 'genres': {}, 'clusters': {}}, {'Lapdance_night': [{'user': '1121800629', 'status': 'INVITED', 'token': 'NBHJUZTRFDSEDFCV'},{'user': 'anja*hh*', 'status': 'REJECTED', 'token': 'GHFRCVGFDE$%RTFG'}],'description': 'Lap to lap', 'genres': {}, 'clusters': {}},{'Partyaninamlparty': [{'user': '1121800629', 'status': 'JOINED', 'token': 'JHGZBVGFDERDXCVDR'}, {'user': 'anja*hh*', 'status': 'INVITED', 'token': 'HGT&/76ghBVGHGFR'}], 'description': 'Calling all animals', 'genres': {}, 'clusters': {}}]

    return data



def save_friendlist_database(database, fileName):

    """ Writes databases as pickled file. Expects database, fileName """

    try:
        with open('data/' + fileName+'.pickle', 'wb') as handle:
            pickle.dump(database, handle, protocol=pickle.HIGHEST_PROTOCOL)
    except:
        logging.info("Saving friendlist failed")
        #logging.info('File name: {}, database {}'.format(fileName, database))
    return
    
    
    
def auto_invite(uid):
    """Helper/dummy function: invites and joins users to a friendlist """


    friendlist_database = load_update_friendlist_database('database_friendlist')
    
    #Initial content
    if not friendlist_database:
        friendlist_database = [{'17hours2hamburg': [{'user': '1121800629', 'status': 'HOST', 'token': '1234567890123455'}, {'user': 'anja*hh*', 'status': 'INVITED', 'token': 'RND16DTOKENJHOKN'}],'description': 'The longer the way, the better the playlist', 'genres': {}, 'clusters': {}},{'The_end_is_near': [{'user': '1121800629', 'status': 'JOINED', 'token': 'JHUNGJOKHNKGOHGS'}, {'user': 'anja*hh*', 'status': 'HOST', 'token': 'HGUJHGZTVBKLOÖMN'}],'description': 'Worlds last best party', 'genres': {}, 'clusters': {}}, {'Lapdance_night': [{'user': '1121800629', 'status': 'INVITED', 'token': 'NBHJUZTRFDSEDFCV'},{'user': 'anja*hh*', 'status': 'REJECTED', 'token': 'GHFRCVGFDE$%RTFG'}],'description': 'Lap to lap', 'genres': {}, 'clusters': {}},{'Partyaninamlparty': [{'user': '1121800629', 'status': 'JOINED', 'token': 'JHGZBVGFDERDXCVDR'}, {'user': 'anja*hh*', 'status': 'INVITED', 'token': 'HGT&/76ghBVGHGFR'}], 'description': 'Calling all animals', 'genres': {}, 'clusters': {}}]

    friendlist_builder = []  #blueprint
    friendlist_feature_builder = {} #blueprint
    friendlist_database_builder = []


    for friendlist_list_object in friendlist_database:
        
        friendlist_itername = (next(iter(friendlist_list_object)))
        friendlist_user_builder = []

        i = friendlist_list_object.get(friendlist_itername)
        i.append({'user': uid, 'status': 'JOINED', 'token': 'JHUNGJOKHNKGOHGS'})

        friendlist_user_builder.append(i)

        friendlist_builder = [{friendlist_itername}] 

        friendlist_builder = {friendlist_itername: friendlist_user_builder[0]}

        for key in friendlist_list_object: #get key/val-Pairs
            if key != friendlist_itername: #Friendlist-name as a dict key is treated diiferently 
                friendlist_feature_builder[key] = friendlist_list_object.get(key) #key/val
                
            friendlist_builder.update(friendlist_feature_builder)
        
        friendlist_database_builder.append(friendlist_builder)
        
    save_friendlist_database('database_friendlist', friendlist_database_builder)


    return(friendlist_database_builder)
    


