from flask import render_template
from app import app
from app.email import send_email

def send_password_reset_email(user):
    token = user.get_reset_password_token()
    if app.config['ADMIN'] == '':
        mailsender = app.config['MAIL_USERNAME']
    else:
        mailsender = app.config['ADMIN']
    send_email('[Tamari] ' + _('Reset Your Password'),
               sender=mailsender,
               recipients=[user.email],
               text_body=render_template('email/set-password.txt',
                                         user=user, token=token),
               html_body=render_template('email/set-password.html',
                                         user=user, token=token))
