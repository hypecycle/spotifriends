import json
import logging
#from jinja2 import Template
from flask import render_template

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


def sendmail(friendlist, friendname, imagepath,friendlistdescription, invitepath):
    msgRoot = MIMEMultipart('related')
    msgRoot['Subject'] = "Testmail"
    msgRoot['From'] = mailclient_login
    msgRoot['To'] = "oheidorn@web.de"
    msgRoot.preamble = 'This is a multi-part message in MIME format.'
    msgAlternative = MIMEMultipart('alternative')
    msgRoot.attach(msgAlternative)
    
    msgText = MIMEText('This is a plain text message that will be generated later.')
    msgAlternative.attach(msgText)
    
    template = render_template('mail_template.html', 
                    friendlist = 'testlist',
                    friendname = 'Aye hombre', 
                    imagepath = 'https://scontent.xx.fbcdn.net/v/t1.0-1/p200x200/19366168_10209376681279499_8387055947959730170_n.jpg?oh=5a9ce2473566985793aaf09a727c6da0&oe=5A95A0BC',
                    friendlistdescription = 'The place to be, the music to listen to',
                    invitepath = 'http://xyz'
                    )
                    
    print(template)

    msgText = MIMEText(template, 'html', "utf-8")
    msgAlternative.attach(msgText)



    
    try:
        server = smtplib.SMTP(mailclient_smtp, mailclient_port)
        server.starttls()
        server.login(mailclient_login, mailclient_pwd)
        server.sendmail(mailclient_login, "oheidorn@web.de", msgRoot.as_string())
        server.quit()
        logging.info("Mailversand OK")          
    except:
        logging.info("Fehler beim Mailversand")
    return
    