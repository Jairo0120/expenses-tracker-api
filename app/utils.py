import re


def remove_spaces(str_to_clean: str) -> str:
    """Function that removes every kind of spaces and returns a clean string"""
    cleaner_str = re.sub(r"[\n\t\r]*", "", str_to_clean)
    return " ".join(cleaner_str.split())
