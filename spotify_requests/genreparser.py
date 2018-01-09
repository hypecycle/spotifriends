from spotify_requests import spotify, responseparser
import logging
import operator

logging.basicConfig(
    filename="aristparser.log",
    level=logging.INFO,
    format="%(asctime)s:%(levelname)s:%(message)s"
    )


#initial definiton: Lordi, Mark Forster, The War on Drugs, Joao Gilberto, Kraftwerk, Theolonius Monk, The Doors, Scooter, Beethoven, Avicii
artists_to_parse = ['14SgKNlOCKAI0PfRD1HnWh', '7qXzy6c5RWT0XlVQcOBIDG', '6g0mn3tzAds6aVeUYRsryU', '0dmPX6ovclgOy8WWJaFEUU', '77ZUbcdoU5KCPHNUl8bgQy', '4PDpGtF16XpqvXxsrFwQnN', '22WZ7M8sxp5THdruNY3gXt', '0HlxL5hisLf59ETEPM3cUA', '2wOqMjp9TyABvtHdOSOTUS', '1vCWHaC5f2uS3yhpwWbIA6']


        
def build_artist_db(auth_header, db_size):
    """Asks spotify for related artists from to-do-list. Stores to database database_artists.pickle
    Finds just 530 genres / 1000 datasets. Maybe combine with build genre_db"""
    
    min_popularity = 20 #if nobody knows, ignore
    
    artist_db = responseparser.load_database('database_artists')   
    a_to_parse = responseparser.load_database('database_artists_to_parse') #to-do-list
    
    if not a_to_parse:
        a_to_parse = ['14SgKNlOCKAI0PfRD1HnWh', '7qXzy6c5RWT0XlVQcOBIDG', '6g0mn3tzAds6aVeUYRsryU', '0dmPX6ovclgOy8WWJaFEUU', '77ZUbcdoU5KCPHNUl8bgQy', '4PDpGtF16XpqvXxsrFwQnN', '22WZ7M8sxp5THdruNY3gXt', '0HlxL5hisLf59ETEPM3cUA', '2wOqMjp9TyABvtHdOSOTUS', '1vCWHaC5f2uS3yhpwWbIA6', '5YGY8feqx7naU7z4HrwZM6', '3RGLhK1IP9jnYFH4BRFJBS', '0oSGxfWSnnOXhD2fKuz2Gy', '4AYkFtEBnNnGuoo8HaHErd']
        #initial definiton: Lordi, Mark Forster, The War on Drugs, Joao Gilberto, Kraftwerk, Theolonius Monk, The Doors, Scooter, Beethoven, Avicii, Miley Cirus, The Clash, Bowie, Madness
        logging.info("a_to_parse empty. init")

 
    a_related = []
    
    while len(artist_db) < db_size: #repeat until db exceeds desired size
           
        response = spotify.get_related_artists(auth_header, a_to_parse[0]) #get rel artists for first in list
        
        #per-build list of related artists beforehand and pre-check
        for artist in response.get('artists'):
            doubleflag = False  
            for acheck in artist_db:
                if next(iter(acheck)) == artist.get('id'):
                    doubleflag = True 
                    
            #if doubleflag:
                #logging.info("genreparser: {} flagged as double".format(artist.get('id')))

            if artist.get('popularity') > min_popularity and not doubleflag:
                a_related.append(artist.get('id'))
                a_builder = {}
                a_id = artist.get('id')
                a_rel_temp = [a for a in a_related if a not in a_id] #ignore the current artist in related list
                a_features = {'artistname': artist.get('name'), 'artisturl': artist.get('external_urls').get('spotify'), 'imageurl': None, 'popularity': artist.get('popularity'), 'followers': artist.get('followers').get('total'), 'genres': artist.get('genres'), 'relatedartists': a_rel_temp}
                a_builder[a_id] = a_features 
                                    
                artist_db.append(a_builder) # write to db          

        logging.info("Got response of {} items, a_related is {}, artist_db is {} a_to_parse is {} ".format(len(response.get('artists')), len(a_related), len(artist_db), len(a_to_parse)))
        a_to_parse = a_to_parse[1:] + a_related #pop the artist already parsed
        a_related = [] #clear for next run
    
                         
    responseparser.save_database('database_artists', artist_db)
    responseparser.save_database('database_artists_to_parse', a_to_parse)    
    logging.info("genreparser: {} artists saved to db".format(len(artist_db)))
      
    return
                
            
def artist_db_overview():
    """Called by dashboard. Returns formatted response"""
    
    artist_db = responseparser.load_database('database_artists')
    response = ''
    
    for artist in artist_db:
        itername = next (iter (artist))
        #response = response + artist.get(itername).get('artistname') + " (" + itername +"), "
        response = response + artist.get(itername).get('artistname') + ", " 
    
    
    return response
    
def count_list(raw_list):
    """expects a list of multiple keywords. returns a dict with:
    'keyword': number_off_occurances """
    
    count_dict = {}
    
    for item in raw_list:
        if item in count_dict:
            count_dict[item] += 1
        else:
            count_dict[item] = 1
            
    return count_dict


def build_genre_db(auth_header):

    """Asks spotify for a list of valid genres for recommendations. 
    Queries artist recommendations for each supergenre. 
    Builds a dict with 'supergenre': ['list of subgenres']
    Counts and weighs artist subgenres. Not called regularly just 
    for upadates. Set is rather small. covers 730 subgenres"""
    
    #query_base serves as prefs for query
    #limit: min 1, default 20, max = 100
    query_base = {
            'min_popularity': 50,
            'limit': 95
            }
            
    query_base_str = ''
    supergenres = {}
    
    #build query for spotify api endpoint
    #try ','.join(item) latrr
    for item in query_base:
	    query_base_str += (item + '=' + str(query_base.get(item))+ '&')

    query_base_str = query_base_str[:-1]

    #gets recommendation super_genres
    response = spotify.get_recommendation_seeds_genres(auth_header).get('genres')
    
    for genre in response:

        logging.info("genreparser: query for {} started".format(genre))
    
        #a_id_list = whole list, a_query = chopped in pieces 0f 50ies
        a_id_list = []
       
        compl_query = "{}&seed_genres={}".format(query_base_str, genre)   
        recommendation = spotify.get_recommendations(auth_header, compl_query)
        #response can have more than 50 items. Artists info can just handle 50!
        
        for i in range(len(recommendation.get('tracks'))):
            #add ids from response to list
            #a little lazy. 'artists' is a list of several artists. 
            #just referencing first in list
            #Maybe just loop over this ?!?!?!
            id = recommendation.get('tracks')[i].get('album').get('artists')[0].get('id')
            a_id_list.append(id)
        
        a_id_pointer = 0
        subgenres = []
        
        #handles queries with more than 50 items and chops them in pcs      
        while len(a_id_list) - a_id_pointer > 0:
            a_query = []
            
            #get_several_artists expects a list, no str
            for i in range(a_id_pointer, a_id_pointer + 50 if a_id_pointer + 50 <= len(a_id_list) else len(a_id_list)):
                a_query.append(a_id_list[i])
            
            a_id_pointer += 50
            
            #queries lists of artist ids. Gets info (including subgenres) in return
            artists = spotify.get_several_artists(auth_header, a_query).get('artists')
            
            for i in range(len(artists)):
                subgenres.extend(artists[i].get('genres'))

        logging.info("genreparser: query for {} returned {} subgenres".format(genre, len(subgenres)))
        
        #returns a dict with ('key': number of occurances)
        subgenres_ct = count_list(subgenres)
        
        supergenres[genre] = subgenres_ct

    responseparser.save_database('database_supergenres', supergenres)
    logging.info("genreparser: {} supergenres saved to tb".format(len(supergenres)))
    
    1/0
        
    return
        
 
def count_genres(database_current_user):

    """receives current user data and returns the genre-count to each user
    Format: {'subgenre1': occurance, ' sg2': occurances …}"""

    genrecount = {}
    
    genrecount_user = {}
    
    user_itername = (next(iter(database_current_user)))
    for tracklist in database_current_user.get(user_itername).get('tracks'):
        for genre in tracklist.get('genres'):               

            if genre in genrecount_user:
                genrecount_user[genre] += 1
            else:
                genrecount_user[genre] = 1

    return genrecount_user    
    

def find_genre_weight(genre_test, top_genres):

    """Find the x best supergenres to fit a users list of subgenres.
    Considerers strong preferrences of a user for certain subgenres. 
    Expects the current user db and number of supergenres to be returned. 
    returns supergenres"""    
    
    #load database that gives a dict of subgenres for each supergenre
    #generated frome time to time in function genreparser.build_genre_db
    genre_db = responseparser.load_database('database_supergenres')  
    user_itername = (next(iter(genre_test)))
    genre_dict = {}

    
    for genre_item_test in genre_test.get(user_itername).get('genres'):
        for supergenre in genre_db:
            for subgenre in genre_db.get(supergenre):
                if genre_item_test in subgenre: #match of subgenres in test and db
                    if supergenre in genre_dict:
                        genre_dict[supergenre] += genre_db.get(supergenre).get(subgenre) * genre_test.get(next(iter(genre_test))).get('genres').get(genre_item_test)
                    else: #empty
                        genre_dict[supergenre] = genre_db.get(supergenre).get(subgenre) * genre_test.get(next(iter(genre_test))).get('genres').get(genre_item_test)

    genres_sorted = sorted(genre_dict.items(), key=operator.itemgetter(1))
    genres_sorted.reverse()
    
    supergenres_top = []
    
    logging.info('genreparser: identified supergenres {}'.format(genres_sorted))

    for key, val in genres_sorted[:top_genres]:
        supergenres_top.append(key)

    return supergenres_top
   