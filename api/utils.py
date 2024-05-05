from datetime import timedelta, date


def get_first_day_month(date_: date) -> date:
    return date(date_.year, date_.month, 1)


def get_last_day_month(date_: date) -> date:
    """
    Given a date, it'll return a new date with the last day of the given date
    """
    month = date_.month
    year = date_.year
    if month == 12:
        month = 1
        year += 1
    else:
        month += 1
    next_month_date = date(year, month, 1)
    return next_month_date - timedelta(days=1)
