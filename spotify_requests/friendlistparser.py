import logging
import datetime

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


