from flask_mail import Message
from app import mail, app
from flask import render_template
from threading import Thread


# Email async function
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


# Main email function (calls async function)
def send_email(subject, sender, recipients, text_body, html_body):
    mail.connect()
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(app, msg)).start()


# sends password reset email
def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email('[Skal] Reset Your Password',
               sender=app.config['ADMINS'][0],
               recipients=[user.email],
               text_body=render_template('email/reset_password.txt',
                                         user=user, token=token),
               html_body=render_template('email/reset_password.html',
                                         user=user, token=token))


# sends verification email
def send_verification_email(user):
    token = user.get_verify_token()
    send_email('[Skal] Verify Your Account',
               sender=app.config['ADMINS'][0],
               recipients=[user.email],
               text_body=render_template('email/verify.txt',
                                         user=user, token=token),
               html_body=render_template('email/verify.html',
                                         user=user, token=token))
