import os
import sys
import utils
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
from app.outlook_email import OutlookEmail
from dotenv import load_dotenv
from cleaning_functions import get_clean_html_body, get_itau_cc_expense


def run():
    load_dotenv()
    """This should call the email service depending on the config set"""
    email_service = OutlookEmail(
        os.getenv('OUTLOOK_USER', ''), os.getenv('OUTLOOK_TOKEN', '')
    )
    email_service.login()
    emails = email_service.get_unseen_emails(os.getenv('INBOX_NAME', 'inbox'))
    emails = utils.filter_messages(
        emails,
        os.getenv('INCLUDED_SUBJECTS', '').split(',')
    )
    for email in emails:
        body = get_clean_html_body(email.message)
        print(body)
        print(get_itau_cc_expense(body))
    pass


if __name__ == '__main__':
    run()
