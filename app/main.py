from outlook_email import OutlookEmail


def run():
    """This should call the email service depending on the config set"""
    email_service = OutlookEmail('test@hotmail.com', 'random-password')
    email_service.login()
    emails = email_service.get_unseen_emails()


run()
