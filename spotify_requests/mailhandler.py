import json
import logging
#from jinja2 import Template
from flask import render_template
from spotify_requests import friendlistparser

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

import smtplib


logging.basicConfig(
    filename="spotifriends.log",
    level=logging.INFO,
    format="%(asctime)s:%(levelname)s:%(message)s"
    )

# client keys
mailclient = json.load(open('conf.json', 'r+'))
mailclient_smtp = mailclient['smtp']
mailclient_pwd = mailclient['mailpwd']
mailclient_login = mailclient['maillogin']
mailclient_port = mailclient['mailport']


def sendmail(friendlistname, friendlistdescription, friends, friendname, imagepath, base):

    for friend in friends:
        msgRoot = MIMEMultipart('related')
        msgRoot['Subject'] = '{} invited you to \"{}\"'.format(friendname, friendlistname)
        msgRoot['From'] = mailclient_login
        msgRoot['To'] = friend.get('invite_mail')
        msgRoot.preamble = 'This is a multi-part message in MIME format.'
        msgAlternative = MIMEMultipart('alternative')
        msgRoot.attach(msgAlternative)
    
        msgText = MIMEText('This is a plain text message that will be generated later.')
        msgAlternative.attach(msgText)
        
        token = friendlistparser.get_token(friendlistname, friend.get('invite_mail'))
        
        url = base + "/profile/invite/" + token 
        
        #placeholder has a relative path
        if imagepath[:7] == '/static': 
            imagepath = base + imagepath
    
        template = render_template('mail_template.html', 
                        friendlistrender = friendlistname,
                        friendrender = friend.get('givenname'),
                        friendlistdescriptionrender = friendlistdescription,
                        friendnamerender = friendname, 
                        imagepathrender = imagepath,
                        urlrender = url
                        )
                    

        msgText = MIMEText(template, 'html', "utf-8")
        msgAlternative.attach(msgText)



    
        try:
            server = smtplib.SMTP(mailclient_smtp, mailclient_port)
            server.starttls()
            server.login(mailclient_login, mailclient_pwd)
            server.sendmail(mailclient_login, friend.get('invite_mail'), msgRoot.as_string())
            server.quit()
            logging.info("Mailversand an {} OK".format(friend.get('invite_mail')))          
        except:
            logging.info("Fehler beim Mailversand an {}".format(friend.get('invite_mail')))
    return
    