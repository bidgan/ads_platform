from redmail import gmail

from main import settings

EMAIL_USER = settings.EMAIL_USER
EMAIL_PASSWORD = settings.EMAIL_PASSWORD


class Email:
    def __init__(self, _receiver, _subject, _message):
        self.username = EMAIL_USER
        self.password = EMAIL_PASSWORD
        self.receiver = _receiver
        self.subject = _subject
        self.message = _message

    def send_email(self):
        gmail.username = self.username
        gmail.password = self.password

        gmail.send(
            subject=self.subject,
            receivers=[self.receiver],
            text=self.message)
