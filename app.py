'''
    This code was based on these repositories,
    so special thanks to:
        https://github.com/mari-linhares/spotify-flask
        https://github.com/datademofun/spotify-flask
        https://github.com/drshrey/spotify-flask-auth-example

'''

from flask import Flask, request, redirect, g, render_template, session, url_for, flash
from wtforms import Form, TextField, TextAreaField, validators, StringField, SubmitField
from spotify_requests import spotify
from spotify_requests import responseparser
from spotify_requests import friendlistparser
from spotify_requests import mailhandler
from spotify_requests import artistparser
import json
import logging


app = Flask(__name__)
app.secret_key = 'sPWLUcu}PdumewjNR9LNYn'

friendList = '' 
database_user = '' 

client = json.load(open('conf.json', 'r+'))
url = client['url']
port = client['port']


base_url = "{}:{}".format(url, port)


class FLForm(Form):
    name = TextField('Name:', validators=[validators.required()])
    description = TextField('Description:', validators=[validators.required()])
    invited_name = TextField('Invited:', validators=[validators.required(), validators.Length(min=3, max=35, message='Name has to be 3 to 35 characters')])
    invited_mail = TextField('Mail:', validators=[validators.required(), validators.Email(message='Please, enter valid email')])
    addfriend = SubmitField(label='Add another friend')
    savefriend = SubmitField(label='Save and invite')

class AddForm(Form):
    invited_name = TextField('Invited:', validators=[validators.required(), validators.Length(min=3, max=35, message='Name has to be 3 to 35 characters')])
    invited_mail = TextField('Mail:', validators=[validators.required(), validators.Email(message='Please, enter valid email')])
    addfriend = SubmitField(label='Add another friend')
    savefriend = SubmitField(label='Save and invite')


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
    #session['name'] = responseparser.parse_name(database_current_user)
    #session['image'] = responseparser.parse_image(database_current_user)
    session['name'] = responseparser.parse_name_pd(profile_data) #new method
    session['image'] = responseparser.parse_image_pd(profile_data) #new method
            
    #Loads existing db, builds db, adds user or replaces user, builds fake_invite
    database_user, known = responseparser.update_main_user_db(database_current_user)
    
    """if not known:
        friendlistparser.auto_invite(session['uid'])
        logging.info("Auto-invited {}".format(session['uid']))"""
    
                
    return profile()

def valid_token(resp):
    return resp is not None and not 'error' in resp

# -------------------------- API REQUESTS ----------------------------


"""@app.route("/")
def index():
    return redirect(url_for('intro_screen'))"""
    
    
@app.route('/profile')
def profile():

    if 'auth_header' in session:
        auth_header = session['auth_header']
        
               
        # get profile data
        profile_data = spotify.get_users_profile(auth_header) #maybe lose this
        uid = profile_data.get('id')
        
        if valid_token(profile_data):
            uid = session['uid']
            new_token = session.get('new_token')
            
            if new_token:
                error = friendlistparser.invite_by_token(new_token, uid)
                session['new_token'] = None
                logging.info("App: New token found. db updated")

            
            friendlist_database = friendlistparser.load_update_friendlist_database('database_friendlist')

            parsed_name_current_user = responseparser.parse_name_pd(profile_data) #maybe replace with session info
            parsed_image_current_user = responseparser.parse_image_pd(profile_data) #maybe replace with session info
            
            friendlist_list = friendlistparser.render_list_of_friendlists(uid)           
            
            return render_template("profile.html",
                                    user = profile_data,
                                    userimage = parsed_image_current_user,
                                    username = parsed_name_current_user,
                                    friendlist_render = friendlist_list)
    else:
        return render_template("profile.html")


@app.route('/profile/invite/<tokenPayload>')

def invite(tokenPayload):

    # only set with fresh token. Deleted, once database is updated
    session['new_token'] = tokenPayload 
    # is set to none, so userbase isn't update in this func call 
    uid = None
    
    #just checking for errors
    error = friendlistparser.invite_by_token(tokenPayload, uid)
    
    if error:
        logging.info("App: error resolving token {}".format(tokenPayload))
        return redirect(url_for('error_invite'))
        
    logging.info("App: Success. Token resolved")
    
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



@app.route('/play')

def play_friendlist():
    if 'auth_header' in session:
        auth_header = session['auth_header']
        
               
        # get profile data
        profile_data = spotify.get_users_profile(auth_header) #maybe lose this
        uid = profile_data.get('id')
        
        if valid_token(profile_data):
            uid = session['uid']
            
            parsed_name_current_user = responseparser.parse_name_pd(profile_data) #maybe replace with session info
            parsed_image_current_user = responseparser.parse_image_pd(profile_data) #maybe replace with session info
                        
            return render_template("play_friendlist.html",
                                    user = profile_data,
                                    userimage = parsed_image_current_user,
                                    username = parsed_name_current_user)
    else:
        return render_template("play_friendlist.html")
        
        
@app.route('/artistdb')

def build_artistdb():

    if 'auth_header' in session:
        auth_header = session['auth_header']
        artistparser.build_artist_db(auth_header, 2000)  
              
    return redirect(url_for('profile'))


@app.route('/genres')

def genre_handling():

    if 'auth_header' in session:
        auth_header = session['auth_header']
        artistparser.build_genre_db(auth_header)  
              
    return redirect(url_for('profile'))
  


@app.route('/new_playlist', methods=['GET', 'POST'])

def new_playlist():

    form = FLForm(request.form)
    logging.info(form.errors)
    uid = session['uid']
    imagepath = session['image']
    error = False
    givenname_invited = []
    mail_invited = []
    friends_to_edit = []
    session.pop('_flashes', None)
    
    
    if request.method == 'POST':
        name=request.form['name']
        description = request.form['description']
        invited_name = request.form['invited_name']
        invited_mail = request.form['invited_mail']

 
        if not form.validate():
            error = True
            for field, errors in form.errors.items():
                for error in errors:
                    flash("Field \'%s\' %s" % (
                        getattr(form, field).label.text,
                        error))
                        
        if friendlistparser.check_friendlist(name):
            error = True
            flash('Friendlist \'' + name + '\' already in use. Choose a new name')
            
        if not error:
            #set name to handle in add_user-form
            session['friendlist_edit'] = name 
            friendlistparser.create_friendlist(name, description, invited_name, invited_mail, session['uid'])

        #when button 'save' is clicked. stores and sends mails
        if not error and form.savefriend.data:
            flash('New friendlist \'' + name + '\' created')
            #friendlistparser.add_friend(name, invited_name, invited_mail)
            friends_to_edit, description_to_edit = friendlistparser.ask_friendlist(name, uid)
            #a = 1/0
            mailhandler.sendmail(name, description_to_edit, friends_to_edit, session.get('name'), imagepath, base_url)
            form.savefriend.data = [] #otherwise it would flash old message
            return redirect(url_for('profile'))
            
        if not error and form.addfriend.data:
            return redirect(url_for('add_user'))

    return render_template('new_playlist.html', 
                            form=form)
                            
@app.route('/add_user', methods=['GET', 'POST'])

def add_user():
    form = AddForm(request.form)
    logging.info(form.errors)
    error = False
    session.pop('_flashes', None)
    
    friendlist_name = session['friendlist_edit']
    uid = session['uid']
    imagepath = session['image']
    friends_to_edit, description_to_edit = friendlistparser.ask_friendlist(friendlist_name, uid)
    
    givenname_invited = []
    mail_invited = []
    
    if request.method == 'POST':
        invited_name = request.form['invited_name']
        invited_mail = request.form['invited_mail']

        if not form.validate():
            error = True
            for field, errors in form.errors.items():
                for error in errors:
                    flash("Field \'%s\' %s" % (
                        getattr(form, field).label.text,
                        error))
                        
        if not error and form.addfriend.data:
            friendlistparser.add_friend(session['friendlist_edit'], invited_name, invited_mail)
            return redirect(url_for('add_user'))
            
        if not error and form.savefriend.data:
            friendlistparser.add_friend(friendlist_name, invited_name, invited_mail)
            friends_to_edit, description_to_edit = friendlistparser.ask_friendlist(friendlist_name, uid)
            mailhandler.sendmail(friendlist_name, description_to_edit, friends_to_edit, session.get('name'), imagepath, base_url)
            form.savefriend.data = [] #otherwise it would flash old message
            return redirect(url_for('profile'))
 
    return render_template('add_user.html', 
                            form=form,
                            friendlist = friendlist_name,
                            friends = friends_to_edit,
                            description = description_to_edit
                            )


@app.route('/error_invite')

def error_invite():
    return render_template('error_invite.html')
 
    
@app.route('/version')
def version_screen():
    return render_template('version.html')
 
@app.route('/intro')   
@app.route('/')
def intro_screen():

    if 'auth_header' in session:
        button1_text = "Continue"
        button2_text = "Logout"
        message1_text = "You are already logged in as {}.".format(session['name'])
        message2_text = "Not you?"
    else:
        button1_text = "Login"
        button2_text = "" #Used as marker. Button
        message1_text = "To find out which music you like, you need to login to spotify."
        message2_text = ""
 
    return render_template('intro.html',
                            button1 = button1_text,
                            button2 = button2_text,
                            message1 = message1_text,
                            message2 = message2_text)
                            
@app.route("/lose_auth")
def lose_auth():
    session.clear() #not really working
    logging.info("deleting auth info")
    return redirect(url_for('intro_screen'))
    
                            
@app.route('/dashboard')
def dashboard_screen():
    if 'auth_header' in session:
        auth_header = session['auth_header']
               
        # get profile data
        profile_data = spotify.get_users_profile(auth_header)      
        
        friendinfo = friendlistparser.render_list_of_friendlists(session['uid'])           

        #Loads existing db, builds db, adds user or replaces user 
        database_user = responseparser.load_database('database_user')
        friendlist_database = friendlistparser.load_update_friendlist_database('database_friendlist')
                            
        return render_template("dashboard.html",
                                user = profile_data,
                                userlist = responseparser.parse_user_list_dashboard(database_user),
                                userimage = session['image'],
                                username = session['name'],
                                dictcheck = database_user,
                                friendlistCheck = friendlist_database,
                                friendinfoCheck = friendinfo,
                                artistcheck = artistparser.artist_db_overview()
                                )

    return render_template('dashboard.html')
    





if __name__ == "__main__":
    #app.run(debug=True, port=spotify.PORT)
    #app.run(host='0.0.0.0', port=spotify.PORT, debug=True)
    app.run(host='0.0.0.0', port=80, debug=True)