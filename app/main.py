import os
import logging
from dotenv import load_dotenv
from src import utils
from src.email_source_mappings import get_all_subjects
from src.email_providers.outlook_email import OutlookEmail
from src.cleaning_functions import get_clean_html_body
from src.target_consumers.expenses_tracker_api import ExpensesTrackerAPI
from src.email_source_mappings import get_cleaning_function
from src.models import Expense


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def main():
    load_dotenv()
    """This should call the email service depending on the config set"""
    email_service = OutlookEmail(
        os.getenv('OUTLOOK_USER', ''), os.getenv('OUTLOOK_TOKEN', ''),
        os.getenv('INBOX_NAME', 'inbox')
    )
    logger.info('Login to email service')
    email_service.login()
    logger.info('Getting unseen emails')
    emails = email_service.get_unseen_emails()
    logger.info('Found %s emails', len(emails))
    emails = utils.filter_messages(emails, get_all_subjects())
    expenses: list[Expense] = []
    et_api = ExpensesTrackerAPI()
    for email in emails:
        body = get_clean_html_body(email.message)
        expense = get_cleaning_function(email.subject)(body)
        expenses.append(expense)
    if et_api.add_expense(expenses=expenses):
        # Marcar como leídos
        pass


if __name__ == '__main__':
    main()
