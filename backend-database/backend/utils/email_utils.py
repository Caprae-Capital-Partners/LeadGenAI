from flask_mail import Mail, Message

mail = Mail()

def init_mail(app):
    mail.init_app(app)


def send_email(subject, recipients, html_body):
    msg = Message(subject, recipients=recipients, html=html_body)
    mail.send(msg)