import pytest
import app.exceptions as exceptions
import tests.mocks.email_mocks as mocks
from app.outlook_email import OutlookEmail


def test_clean_message_body_error():
    """
    Test that the function raises an error when this doesn't find any html body
    tag in the email message
    """
    oe = OutlookEmail('', '')
    with pytest.raises(exceptions.UnableGetBodyMessageException):
        oe.get_clean_html_body(mocks.BAD_EMAIL)


def test_clean_message_body_returns_empty_body():
    """
    Test that the function returns an empty string when the content of a
    email message is empty between the body tag
    """
    oe = OutlookEmail('', '')
    email_body = oe.get_clean_html_body(mocks.GOOD_EMPTY_EMAIL)
    assert email_body == ''


def test_clean_message_body_returns_body():
    """
    Test that the function returns the content inside the body tag of the
    raw email message
    """
    oe = OutlookEmail('', '')
    expected = '''
    <h1>Some header</h1>
    <div class="some-class" id="some-id">Some random content</div>
    <section>Some text for this section</section>
    <table><thead><th>Some column</th></thead><tbody><tr><td>Some content</td>
    </tr></tbody></table>
    <footer>
    Some footer
    </footer>
    '''
    email_body = oe.get_clean_html_body(mocks.GOOD_FULL_EMAIL)
    assert email_body == expected
