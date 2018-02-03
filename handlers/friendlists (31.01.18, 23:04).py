from handlers import databases
import itertools
import logging


logging.basicConfig(
    filename="spotifriends.log",
    level=logging.INFO,
    format="%(asctime)s:%(levelname)s:%(message)s"
    )

def find_common_songs(friendlist):

	"""
	Takes the friendDB and looks for the entry of the relevant
	Friendlist. Then parses out all friends in the list
	The list's friend's IDs, Names and a list of track IDs
	are stored in separate list variables

	Builds a list 'trackDict' with all IDs: Names 
	to pair the IDs with the right Trackname

	"""

	# Get Databases
	friendDB = databases.load_database('database_friendlist') 
	userDb = databases.load_database('database_user') 

	friendsInList = []
	friendsTrack =[]
	friendsNames = []
	nameInList = []
	foundTrackID = []
	foundTrackList = []
	trackDict = {}


	for friendListItem in friendDB: 
		if (next(iter(friendListItem))) == friendlist:
			for friend in friendListItem.get(friendlist):

				friendUID = friend.get('user')
				friendsInList.append(friendUID)

				for userDat in userDb:
					if friendUID == next(iter(userDat)):
						trackListTemp = userDat.get(friendUID).get('tracks')
						trackTemp = []
						for track in trackListTemp:
							trackTemp.append(track.get('trackid'))
							trackDict[track.get('trackid')] = track.get('trackname')
						friendsTrack.append(trackTemp)
						friendsNames.append(userDat.get(friendUID)
									.get('cumulated_name'))

	# Generates a list of every title that appeared twice 
	for user1, user2 in itertools.combinations(range(len(friendsInList)), 2):
		foundTrackID += (list(set(friendsTrack[user1])
							.intersection((friendsTrack[user2]))))

	
	# Skip doubles 
	check = set()
	foundTrackIDUniq = [x for x in foundTrackID if x not in check and not check.add(x)] 


	# Loop over the user's tracklists to find out if an ID
	# appears in his list. If Yes, store name, ID and tracksID
	# in a dict.

	for foundTrack in foundTrackIDUniq:
		foundTrackListBuilder = {'track': foundTrack, 
								 'trackname': trackDict.get(foundTrack),
								 'uid': [], 'cumulated_name': [],
								 }


		for i in range(len(friendsInList)):
			if foundTrack in friendsTrack[i]:
				foundTrackListBuilder['uid'].append(friendsInList[i])
				foundTrackListBuilder['cumulated_name'].append(friendsNames[i])

		foundTrackList.append(foundTrackListBuilder)
	      
	return foundTrackList




