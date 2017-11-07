'''
    This code was based on these repositories,
    so special thanks to:
        https://github.com/datademofun/spotify-flask
        https://github.com/drshrey/spotify-flask-auth-example

'''

from flask import Flask, request, redirect, g, render_template, session
from spotify_requests import spotify
from spotify_requests import responseparser

app = Flask(__name__)
app.secret_key = 'some key for session'

friendList = '17hours2hamburg' # fix during prototype. 
friendListDescr = 'The longer the way, the better the music needs to be' #fix during pt

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


@app.route('/profile')
def profile():
    if 'auth_header' in session:
        auth_header = session['auth_header']
        # get profile data
        profile_data = spotify.get_users_profile(auth_header)

        # get user playlist data
        playlist_data = spotify.get_users_playlists(auth_header)

        # get user recently played tracks
        recently_played = spotify.get_users_recently_played(auth_header)

        if valid_token(recently_played):
            return render_template("profile.html",
                               user=profile_data,
                               playlists=playlist_data["items"],
                               recently_played=recently_played["items"])

    return render_template('profile.html')
    

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
    
@app.route('/intro')
def intro_screen():
    return render_template('intro_screen.html', 
    						friendListRender = friendList,
    						friendListDescrRender = friendListDescr)
    						
@app.route('/loading')
def loading_screen():
    if 'auth_header' in session:
        auth_header = session['auth_header']
               
        # get profile data
        profile_data = spotify.get_users_profile(auth_header)
        
        # get top tracks
        track_data = spotify.get_users_top(auth_header, 'tracks', 3)
        
        #database = responseparser.init_database(auth_header,friendList, friendListDescr)
        #database = "Foo"

        if valid_token(profile_data): 
            return render_template("loading_screen.html",
            					friendListHeaderRender = friendList,
                                user=profile_data,
                                tracks = track_data)

    return render_template('loading_screen.html')
    

@app.route('/dash')
def dashboard_screen():
    if 'auth_header' in session:
        auth_header = session['auth_header']
               
        # get profile data
        profile_data = spotify.get_users_profile(auth_header)
        
        #database = responseparser.init_database(auth_header,friendList, friendListDescr)
        #database = "Foo"

        if valid_token(profile_data): 
            return render_template("dashboard.html",
            					friendListHeaderRender = friendList,
                                databaseRender = database)

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