from flask_mail import Message
from flask import render_template
from app import mail, app
from threading import Thread

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    app.logger.info(
        'Queueing email: subject=%s sender_configured=%s recipient_count=%s',
        subject,
        bool(sender),
        len(recipients)
    )
    Thread(target=send_async_email, args=(app, msg)).start()

def send_async_email(app, msg):
    with app.app_context():
        try:
            app.logger.info(
                'Sending email: subject=%s recipient_count=%s',
                msg.subject,
                len(msg.recipients)
            )
            mail.send(msg)
            app.logger.info(
                'Email accepted by SMTP server: subject=%s',
                msg.subject
            )
        except Exception:
            app.logger.exception(
                'Email delivery failed: subject=%s',
                msg.subject
            )