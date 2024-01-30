import os
from src import utils
from src.outlook_email import OutlookEmail
from src.cleaning_functions import get_clean_html_body, get_itau_cc_expense
from dotenv import load_dotenv


def main():
    load_dotenv()
    """This should call the email service depending on the config set"""
    email_service = OutlookEmail(
        os.getenv('OUTLOOK_USER', ''), os.getenv('OUTLOOK_TOKEN', '')
    )
    exit(0)
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
    main()
