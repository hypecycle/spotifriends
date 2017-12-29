from spotify_requests import spotify, responseparser
import logging

logging.basicConfig(
    filename="aristparser.log",
    level=logging.INFO,
    format="%(asctime)s:%(levelname)s:%(message)s"
    )


#initial definiton: Lordi, Mark Forster, The War on Drugs, Joao Gilberto, Kraftwerk, Theolonius Monk, The Doors, Scooter, Beethoven, Avicii
artists_to_parse = ['14SgKNlOCKAI0PfRD1HnWh', '7qXzy6c5RWT0XlVQcOBIDG', '6g0mn3tzAds6aVeUYRsryU', '0dmPX6ovclgOy8WWJaFEUU', '77ZUbcdoU5KCPHNUl8bgQy', '4PDpGtF16XpqvXxsrFwQnN', '22WZ7M8sxp5THdruNY3gXt', '0HlxL5hisLf59ETEPM3cUA', '2wOqMjp9TyABvtHdOSOTUS', '1vCWHaC5f2uS3yhpwWbIA6']


        
def build_artist_db(auth_header, db_size):
    """Asks spotify for related artists from to-do-list. Stores to database database_artists.pickle"""
    
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
                #logging.info("artistparser: {} flagged as double".format(artist.get('id')))

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
    logging.info("artistparser: {} artists saved to db".format(len(artist_db)))
      
    return
                
            
def artist_db_overview():
    """Called by dashboard. Returns formatted response"""
    
    artist_db = responseparser.load_database('database_artists')
    response = ''
    
    for artist in artist_db:
        itername = next (iter (artist))
        response = response + artist.get(itername).get('artistname') + " (" + itername +"), "
        #response = response + artist.get(itername).get('artistname') + ", " 
    
    
    return response


def build_genre_db(auth_header):

    """Asks spotify for a list of valid genres for recommendations. 
    Queries artist recommendations for each supergenre. 
    Counts and weighs artist subgenres."""
    
    #query_base serves as prefs for query
    #limit: min 1, default 20, max = 100
    query_base = {
            'min_popularity': 50,
            'limit': 50
            }
            
    query_base_str = ''
    
    #build query for spotify api endpoint
    for item in query_base:
	    query_base_str += (item + '=' + str(query_base.get(item))+ '&')

    query_base_str = query_base_str[:-1]

    #gets recommendation super_genres
    response = spotify.get_recommendation_seeds_genres(auth_header).get('genres')
    
    for genre in response:
    
        a_id_list = []
       
        compl_query = "{}&seed_genres={}".format(query_base_str, genre)   
        recommendation = spotify.get_recommendations(auth_header, compl_query)
        #response can have more than 50 items. Artists info can just handle 50!
        
        for i in range(len(recommendation.get('tracks'))):
            #add ids from response to list
            id = recommendation.get('tracks')[i].get('album').get('id')
            a_id_list.append(id)
        
        a_id_pointer = 0
        
        #handles queries with more than 50 items and chops them in pcs      
        while len(a_id_list) - a_id_pointer > 0:
            a_query = ''
            
            for i in range(a_id_pointer, a_id_pointer + (len(a_id_list) - a_id_pointer)):
                a_query += a_id_list[i]+','
                
            a_query = a_query[:-1]
            a_id_pointer += 50
            
            #queries lists of artist ids. Gets info (including subgenres) in return
            artists = get_several_artists(auth_header, list_of_ids) 
            
        1/0
        
    return
        
        