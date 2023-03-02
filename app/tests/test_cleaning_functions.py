import re
import pytest
import app.exceptions as exceptions
import app.tests.mocks.email_mocks as mocks
from app.cleaning_functions import get_clean_html_body, get_itau_cc_expense
from app.models import Expense
from datetime import datetime


def test_clean_message_body_error():
    """
    Test that the function raises an error when this doesn't find any html body
    tag in the email message
    """
    with pytest.raises(exceptions.UnableGetBodyMessageException):
        get_clean_html_body(mocks.BAD_EMAIL)


def test_clean_message_body_incomplete():
    """
    Test that the function raises an error when this doesn't find a good html
    content inside the email message
    """
    with pytest.raises(exceptions.UnableGetBodyMessageException):
        get_clean_html_body(mocks.INCOMPLETE_HTML_EMAIL)


def test_clean_message_missing_body():
    """
    Test that the function raises an error when this doesn't find a body inside
    the html content of the email
    """
    with pytest.raises(exceptions.UnableGetBodyMessageException):
        get_clean_html_body(mocks.MISSING_HTML_BODY_EMAIL)


def test_clean_message_body_returns_empty_body():
    """
    Test that the function returns an empty string when the content of a
    email message is empty between the body tag
    """
    expected = '''
    <body bgcolor="#ffffff" style="background-color: #ffffff;
    color: #000000; padding: 0px; -webkit-text-size-adjust:none;
    font-size: 16px; font-family:arial,helvetica,sans-serif;" text="#000000">
    </body>
    '''
    email_body = get_clean_html_body(mocks.GOOD_EMPTY_EMAIL)
    assert re.sub(r"[\s]*", "", email_body) == \
           re.sub(r"[\s]", "", expected)


def test_clean_message_body_returns_body():
    """
    Test that the function returns the content inside the body tag of the
    raw email message
    """
    expected = '''
    <body>
    <h1>Some header</h1>
    <div class="some-class" id="some-id">Some random content</div>
    <section>Some text for this section</section>
    <table><thead><th>Some column</th></thead><tbody><tr><td>Some content</td>
    </tr></tbody></table>
    <footer>
    Some footer
    </footer>
    </body>
    '''
    email_body = get_clean_html_body(mocks.GOOD_FULL_EMAIL)
    assert re.sub(r"[\s]*", "", email_body) == \
           re.sub(r"[\s]", "", expected)


def test_itau_extracted_expense_wrong_format():
    """
    Test that the function raises an exception when the expenses email from
    Itau doesn't have the right format
    """
    with pytest.raises(exceptions.UnableGetExpenseException):
        get_itau_cc_expense(mocks.ITAU_BAD_TABLE_STRUCTURE)


def test_itau_extracted_expense_bad_value():
    """
    Test that the function raises an error when the value of the expense
    hasn't a right numeric format
    """
    with pytest.raises(exceptions.UnableGetExpenseException):
        get_itau_cc_expense(mocks.ITAU_BAD_EXPENSE_VALUE)


def test_itau_extracted_date_bad_value():
    """
    Test that the function raises an error when the value of the date of the
    expense hasn't the right format (DD/MM/YYYY HH24:MI:SS)
    """
    with pytest.raises(exceptions.UnableGetExpenseException):
        get_itau_cc_expense(mocks.ITAU_BAD_DATE_VALUE)


def test_itau_expense_extracted_success():
    """Test the case when the date is right in the itau email message"""
    expected = Expense(
        expense_value=29300.21,
        description=('Se realizó una compra en DIDI FOOD*DL desde tu Tarjeta'
                     ' Credito número *****7651 de Itaú:'),
        date_expense=datetime(2023, 2, 14, 18, 25, 12)
    )
    assert expected == get_itau_cc_expense(mocks.ITAU_GOOD_TABLE_STRUCTURE)
