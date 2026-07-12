from flask import render_template
from app import app
from app.email import send_email
from app.models import User
from flask_babel import _

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

def send_registration_set_password_email(email):
    token = User.get_registration_token(email)
    if app.config['ADMIN'] == '':
        mailsender = app.config['MAIL_USERNAME']
    else:
        mailsender = app.config['ADMIN']
    send_email('[Tamari] ' + _('Set Your Password'),
               sender=mailsender,
               recipients=[email],
               text_body=render_template('email/register-set-password.txt',
                                         token=token),
               html_body=render_template('email/register-set-password.html',
                                         token=token))
