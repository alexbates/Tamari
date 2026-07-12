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
    send_email(
        '[Tamari] ' + _('Reset Your Password'),
        sender=mailsender,
        recipients=[user.email],
        text_body=render_template(
            'email/set-password.txt',
            user=user, token=token
        ),
        html_body=render_template(
            'email/set-password.html',
            user=user, token=token
        )
    )

def send_registration_set_password_email(email):
    token = User.get_registration_token(email)
    if app.config['ADMIN'] == '':
        mailsender = app.config['MAIL_USERNAME']
    else:
        mailsender = app.config['ADMIN']
    send_email(
        '[Tamari] ' + _('Set Your Password'),
        sender=mailsender,
        recipients=[email],
        text_body=render_template(
            'email/register-set-password.txt',
            token=token
        ),
        html_body=render_template(
            'email/register-set-password.html',
            token=token
        )
    )

def send_email_change_verification_email(user, new_email):
    token = user.get_email_change_token(new_email)
    if app.config['ADMIN'] == '':
        mailsender = app.config['MAIL_USERNAME']
    else:
        mailsender = app.config['ADMIN']
    send_email(
        '[Tamari] ' + _('Confirm Your Email Change'),
        sender=mailsender,
        recipients=[new_email],
        text_body=render_template(
            'email/verify-email-change.txt',
            token=token
        ),
        html_body=render_template(
            'email/verify-email-change.html',
            token=token
        )
    )