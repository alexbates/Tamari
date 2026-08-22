from flask import render_template, current_app, url_for
from app import app
from app.email import send_email
from app.models import User
from flask_babel import _

def get_public_url(endpoint, token):
    public_url = current_app.config.get('PUBLIC_URL')
    if not public_url:
        current_app.logger.error(
            'Account email not sent because PUBLIC_URL is not configured.'
        )
        return None
    if not public_url.startswith(('http://', 'https://')):
        current_app.logger.error(
            'Account email not sent because PUBLIC_URL must begin with http:// or https://.'
        )
        return None
    path = url_for(endpoint, token=token, _external=False)
    return public_url.rstrip('/') + path

def send_password_reset_email(user):
    token = user.get_reset_password_token()
    reset_url = get_public_url('account.set_password', token)
    if reset_url is None:
        return
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
            user=user, reset_url=reset_url
        ),
        html_body=render_template(
            'email/set-password.html',
            user=user, reset_url=reset_url
        )
    )

def send_registration_set_password_email(email):
    token = User.get_registration_token(email)
    registration_url = get_public_url('account.register_set_password', token)
    if registration_url is None:
        return
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
            registration_url=registration_url
        ),
        html_body=render_template(
            'email/register-set-password.html',
            registration_url=registration_url
        )
    )

def send_email_change_verification_email(user, new_email):
    token = user.get_email_change_token(new_email)
    email_change_url = get_public_url('account.verify_email_change', token)
    if email_change_url is None:
        return
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
            email_change_url=email_change_url
        ),
        html_body=render_template(
            'email/verify-email-change.html',
            email_change_url=email_change_url
        )
    )