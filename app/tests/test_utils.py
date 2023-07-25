from app.utils import remove_spaces, filter_messages
from app.models import EmailMessage


def test_remove_spaces_success_multiple_spaces():
    input_val = '   Hola \t\n mundo, \r   esta  es una       Prueba'
    assert 'Hola mundo, esta es una Prueba' == remove_spaces(input_val)


def test_remove_spaces_success_multiple_break_lines():
    input_val = ('\n\r  Hola \t\n mundo\n\n\n... \r  '
                 'esta  es una   \r\t\t  Prueba')
    assert 'Hola mundo... esta es una Prueba' == remove_spaces(input_val)


def test_remove_spaces_empty_string():
    assert '' == remove_spaces('')


def test_filter_messages_empty_lists():
    """Test when there are no messages and included_subjects"""
    assert filter_messages([], []) == []


def test_filter_messages_no_subjects():
    """
    Test when there are no included_subjects, so all messages should be
    filtered out
    """
    messages = [
        EmailMessage(id='1', subject="Hello", message="Body 1"),
        EmailMessage(id='2', subject="Hi", message="Body 2"),
    ]
    assert filter_messages(messages, []) == []


def test_filter_messages_no_matching_subjects():
    """Test when there are no messages with matching subjects"""
    messages = [
        EmailMessage(id='1', subject="Hello", message="Body 1"),
        EmailMessage(id='2', subject="Hi", message="Body 2"),
    ]
    included_subjects = ["important", "urgent"]
    assert filter_messages(messages, included_subjects) == []


def test_filter_messages_matching_subjects():
    """Test when there are messages with matching subjects"""
    messages = [
        EmailMessage(id='1', subject="Hello, urgent!", message="Body 1"),
        EmailMessage(id='2', subject="Hi, important topic", message="Body 2"),
        EmailMessage(id='3', subject="General update", message="Body 3"),
    ]
    included_subjects = ["important", "urgent"]
    filtered_messages = filter_messages(messages, included_subjects)
    # Ensure that the filtered messages contain only those with matching
    # subjects
    assert len(filtered_messages) == 2
    assert all(msg in messages for msg in filtered_messages)


def test_filter_messages_matching_subjects_case_insensitive():
    """Test when included_subjects contain uppercase characters"""
    messages = [
        EmailMessage(id='1', subject="Hello, urgent!", message="Body 1"),
        EmailMessage(id='2', subject="Hi, important topic", message="Body 2"),
        EmailMessage(id='3', subject="General update", message="Body 3"),
    ]
    included_subjects = ["Important", "uRgEnt"]
    filtered_messages = filter_messages(messages, included_subjects)
    # Ensure that the filtered messages contain only those with matching
    # subjects
    assert len(filtered_messages) == 2
    assert filtered_messages[0].id == '1'
    assert filtered_messages[1].id == '2'
    assert all(msg in messages for msg in filtered_messages)
