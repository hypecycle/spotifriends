'''
    This code was based on these repositories,
    so special thanks to:
        https://github.com/datademofun/spotify-flask
        https://github.com/drshrey/spotify-flask-auth-example

'''

from flask import Flask, request, redirect, g, render_template, session
from spotify_requests import spotify
from spotify_requests import responseparser
from spotify_requests import friendlistparser

app = Flask(__name__)
app.secret_key = 'some key for session'

friendList = '17hours2hamburg' # fix during prototype. 
friendListDescr = 'The longer the way, the better the music needs to be' #fix during pt


friendlist_database = [{'17hours2hamburg': [{'user': '1121800629', 'status': 'HOST', 'token': '1234567890123455'}, {'user': 'anja*hh*', 'status': 'INVITED', 'token': 'RND16DTOKENJHOKN'}],'description': 'The longer the way, the better the playlist', 'genres': {}, 'clusters': {}},{'The_end_is_near': [{'user': '1121800629', 'status': 'JOINED', 'token': 'JHUNGJOKHNKGOHGS'}, {'user': 'anja*hh*', 'status': 'HOST', 'token': 'HGUJHGZTVBKLOÖMN'}],'description': 'Worlds last best party', 'genres': {}, 'clusters': {}}, {'Lapdance_night': [{'user': '1121800629', 'status': 'INVITED', 'token': 'NBHJUZTRFDSEDFCV'},{'user': 'anja*hh*', 'status': 'REJECTED', 'token': 'GHFRCVGFDE$%RTFG'}],'description': 'Lap to lap', 'genres': {}, 'clusters': {}},{'Partyaninamlparty': [{'user': '1121800629', 'status': 'JOINED', 'token': 'JHGZBVGFDERDXCVDR'}, {'user': 'anja*hh*', 'status': 'INVITED', 'token': 'HGT&/76ghBVGHGFR'}], 'description': 'Calling all animals', 'genres': {}, 'clusters': {}}]

# ----------------------- AUTH API PROCEDURE -------------------------

@app.route("/auth")
def auth():
    return redirect(spotify.AUTH_URL)


@app.route("/callback/")
def callback():

    auth_token = request.args['code']
    auth_header = spotify.authorize(auth_token)
    session['auth_header'] = auth_header

    return profile()

def valid_token(resp):
    return resp is not None and not 'error' in resp

# -------------------------- API REQUESTS ----------------------------


@app.route("/")
def index():
    return render_template('index.html')



@app.route('/artist/<id>')
def artist(id):
    artist = spotify.get_artist(id)

    if artist['images']:
        image_url = artist['images'][0]['url']
    else:
        image_url = 'http://bit.ly/2nXRRfX'

    tracksdata = spotify.get_artist_top_tracks(id)
    tracks = tracksdata['tracks']

    related = spotify.get_related_artists(id)
    related = related['artists']

    return render_template('artist.html',
                           artist=artist,
                           related_artists=related,
                           image_url=image_url,
                           tracks=tracks)
    

@app.route('/profile2')
def profile2():
    if 'auth_header' in session:
        auth_header = session['auth_header']
               
        # get profile data
        profile_data = spotify.get_users_profile(auth_header)
        
        database = responseparser.init_database(auth_header,friendList, friendListDescr)
        #database = "Foo"

        if valid_token(profile_data): 
            return render_template("profile2.html",
                                user=profile_data,
                                tracklist = profile_data,
                                dictcheck = database)

    return render_template('profile2.html')
    
    
@app.route('/profile')
def profile():
	if 'auth_header' in session:
		auth_header = session['auth_header']
               
		# get profile data
		profile_data = spotify.get_users_profile(auth_header)        

		if valid_token(profile_data): 
        	
			#Requests all data from spotify and forms a dict
			database_current_user, uid = responseparser.get_user_data(auth_header, profile_data)
            
			#Loads existing db, builds db, adds user or replaces user 
			database_user = responseparser.update_main_user_db(database_current_user)
            
			#display ANY name, even for user which names are not set 1. Display name, 2. Given name, 3. UID
			parsed_name_current_user = responseparser.parse_name(database_current_user)
            
			parsed_image_current_user = responseparser.parse_image(database_current_user)
			
			friendlist_list = friendlistparser.render_list_of_friendlists(friendlist_database, uid)
			
            
			return render_template("profile.html",
								user = profile_data,
								userimage = parsed_image_current_user,
								username = parsed_name_current_user,
								friendlist_render = friendlist_list)

	return render_template('profile.html')
    
    
    
@app.route('/intro')
def intro_screen():
    return render_template('intro.html')
    
    						
@app.route('/dash')
def dashboard_screen():
    if 'auth_header' in session:
        auth_header = session['auth_header']
               
        # get profile data
        profile_data = spotify.get_users_profile(auth_header)        

        if valid_token(profile_data): 
        	
        	#Requests all data from spotify and forms a dict
            database_current_user, uid = responseparser.get_user_data(auth_header, profile_data)
            
            #Loads existing db, builds db, adds user or replaces user 
            database_user = responseparser.update_main_user_db(database_current_user)
            
            #display ANY name, even for user which names are not set 1. Display name, 2. Given name, 3. UID
            parsed_name_current_user = responseparser.parse_name(database_current_user)
            
            parsed_image_current_user = responseparser.parse_image(database_current_user)
            
            return render_template("dashboard.html",
            					user = profile_data,
            					userlist = responseparser.parse_user_list_dashboard(database_user),
                                userimage = parsed_image_current_user,
                                username = parsed_name_current_user,
                                dictcheck = database_user)

    return render_template('dashboard.html')
    



@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/featured_playlists')
def featured_playlists():
    if 'auth_header' in session:
        auth_header = session['auth_header']
        hot = spotify.get_featured_playlists(auth_header)
        if valid_token(hot):
            return render_template('featured_playlists.html', hot=hot)

    return render_template('profile.html')

if __name__ == "__main__":
    #app.run(debug=True, port=spotify.PORT)
    #app.run(host='0.0.0.0', port=spotify.PORT, debug=True)
    app.run(host='0.0.0.0', port=80, debug=True)