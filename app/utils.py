import re
from app.models import EmailMessage


def remove_spaces(str_to_clean: str) -> str:
    """Function that removes every kind of spaces and returns a clean string"""
    cleaner_str = re.sub(r"[\n\t\r]*", "", str_to_clean)
    return " ".join(cleaner_str.split())


def filter_messages(messages: list[EmailMessage],
                    included_subjects: list[str]) -> list[EmailMessage]:
    filtered_messages: list[EmailMessage] = []
    # We could simplify this nested loop with list comprenhensions and the
    # any function, but this is more readable
    for message in messages:
        for included_subject in included_subjects:
            if included_subject.lower() in message.subject.lower():
                filtered_messages.append(message)
                break
    return filtered_messages
