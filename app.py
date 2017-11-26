'''
    This code was based on these repositories,
    so special thanks to:
        https://github.com/datademofun/spotify-flask
        https://github.com/drshrey/spotify-flask-auth-example

'''

from flask import Flask, request, redirect, g, render_template, session, url_for
from spotify_requests import spotify
from spotify_requests import responseparser
from spotify_requests import friendlistparser
import logging


app = Flask(__name__)
app.secret_key = 'sPWLUcu}PdumewjNR9LNYn'

friendList = '' 
database_user = '' 
checkint = 0 #temp
closeint = 0 #temp

friendlist_database = [{'17hours2hamburg': [],'description': 'The longer the way, the better the playlist', 'genres': {}, 'clusters': {}},{'The_end_is_near': [],'description': 'Worlds last best party', 'genres': {}, 'clusters': {}}, {'Lapdance_night': [],'description': 'Lap to lap', 'genres': {}, 'clusters': {}},{'Partyaninamlparty': [], 'description': 'Calling all animals', 'genres': {}, 'clusters': {}}]


logging.basicConfig(
    filename="spotifriends.log",
    level=logging.INFO,
    format="%(asctime)s:%(levelname)s:%(message)s"
    )

# ----------------------- AUTH API PROCEDURE ------------------------

@app.route("/auth")
def auth():
    logging.info("auth entered")
    return redirect(spotify.AUTH_URL)


@app.route("/callback/")
def callback():

    auth_token = request.args['code']
    auth_header = spotify.authorize(auth_token)
    session['auth_header'] = auth_header
    
    #get profile_data first – basic for spotify call
    profile_data = spotify.get_users_profile(auth_header)
    #uid = profile_data.get('id')
    
    
    #------- new login? Resets database_current_user, uid, database_user
    #getting user data, parse and save it
    #Requests all data from spotify and forms a dict
    database_current_user, uid = responseparser.get_user_data(auth_header, profile_data)
    session['uid'] = uid
    
    logging.info("Callback entered for {}".format(session['uid']))
    
    #writing crucial data do session to make it available everywhere
    session['name'] = responseparser.parse_name(database_current_user)
    session['image'] = responseparser.parse_image(database_current_user)
            
    #Loads existing db, builds db, adds user or replaces user, builds fake_invite
    database_user, known = responseparser.update_main_user_db(database_current_user)
    
    if not known:
        friendlistparser.auto_invite(session['uid'])
        logging.info("Auto-invited {}".format(session['uid']))
    
                
    return profile()

def valid_token(resp):
    return resp is not None and not 'error' in resp

# -------------------------- API REQUESTS ----------------------------


@app.route("/")
def index():
    return render_template('index.html')
    
    
@app.route('/profile')
def profile():
    if 'auth_header' in session:
        auth_header = session['auth_header']
        
               
        # get profile data
        profile_data = spotify.get_users_profile(auth_header)
        uid = profile_data.get('id')
        
        friendlist_database = friendlistparser.load_update_friendlist_database('database_friendlist')

        parsed_name_current_user = responseparser.parse_name_pd(profile_data)    
        parsed_image_current_user = responseparser.parse_image_pd(profile_data)
            
        friendlist_list = friendlistparser.render_list_of_friendlists(friendlist_database, uid)
            
            
        return render_template("profile.html",
                                user = profile_data,
                                userimage = parsed_image_current_user,
                                username = parsed_name_current_user,
                                friendlist_render = friendlist_list)
    else:
        return render_template("profile.html")


@app.route('/profile/invite/<tokenPayload>')

def invite(tokenPayload):
    
    invited_user, invited_friendList, error = friendlistparser.resolve_token(tokenPayload)

    if error:
        return redirect(url_for('error_invite'))
        
    friendlist_database_new = friendlistparser.update_friendlist(friendlistparser.load_update_friendlist_database('database_friendlist'), invited_friendList, invited_user, 'INVITED')
    friendlistparser.save_friendlist_database(friendlist_database_new, 'database_friendlist')

    logging.info("App: Success. Invited {} by link".format(session['invited_user']))
    
    return redirect(url_for('profile'))


    
@app.route('/profile/join/<uidPayload>/<friendListPayload>')

def accept(friendListPayload, uidPayload):
    
    friendlist_database_new = friendlistparser.update_friendlist(friendlistparser.load_update_friendlist_database('database_friendlist'), friendListPayload, uidPayload, 'JOINED')
    friendlistparser.save_friendlist_database(friendlist_database_new, 'database_friendlist')
    return redirect(url_for('profile'))
    
    
@app.route('/profile/reject/<uidPayload>/<friendListPayload>')

def reject(friendListPayload, uidPayload):

    friendlist_database_new = friendlistparser.update_friendlist(friendlistparser.load_update_friendlist_database('database_friendlist'), friendListPayload, uidPayload, 'REJECTED')
    friendlistparser.save_friendlist_database(friendlist_database_new, 'database_friendlist')
    return redirect(url_for('profile'))



@app.route('/testbutton/<payload>')

def test_button(payload):

    return render_template('test_button.html', pay = payload)
    
    
    
@app.route('/error_invite')

def error_invite():
    return render_template('error_invite.html')
 
    
@app.route('/version')
def version_screen():
    return render_template('version.html')
    
@app.route('/intro')
def intro_screen():
    return render_template('intro.html')
    
                            
@app.route('/dashboard')
def dashboard_screen():
    if 'auth_header' in session:
        auth_header = session['auth_header']
               
        # get profile data
        profile_data = spotify.get_users_profile(auth_header)      
        

        #Loads existing db, builds db, adds user or replaces user 
        database_user = responseparser.load_database('database_user')
        friendlist_database = friendlistparser.load_update_friendlist_database('database_friendlist')
                    
        return render_template("dashboard.html",
                                user = profile_data,
                                userlist = responseparser.parse_user_list_dashboard(database_user),
                                userimage = session['image'],
                                username = session['name'],
                                dictcheck = database_user,
                                friendlistCheck = friendlist_database)

    return render_template('dashboard.html')
    





if __name__ == "__main__":
    #app.run(debug=True, port=spotify.PORT)
    #app.run(host='0.0.0.0', port=spotify.PORT, debug=True)
    app.run(host='0.0.0.0', port=80, debug=True)