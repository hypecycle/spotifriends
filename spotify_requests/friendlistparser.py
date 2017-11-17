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