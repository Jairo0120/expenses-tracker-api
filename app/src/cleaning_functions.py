import re
from src.exceptions import (
    UnableGetExpenseException, UnableGetBodyMessageException
)
from src.models import Expense
from src import utils
from bs4 import BeautifulSoup
from datetime import datetime


def get_clean_html_body(raw_message: str) -> str:
    html_index = raw_message.find('<html')
    if html_index < 0:
        raise UnableGetBodyMessageException
    html_content = raw_message[html_index:]
    soup = BeautifulSoup(html_content, 'html.parser')
    body_tag = soup.find('body')
    if not body_tag:
        raise UnableGetBodyMessageException
    return str(body_tag)


def get_itau_cc_expense(message_body: str) -> Expense:
    """
    Function to return an expense filtering the info from an Itau
    credit card expense
    """
    soup = BeautifulSoup(message_body, 'html.parser')
    expense = Expense(0, '')
    tables = soup.find_all('table')
    expense_value = ''
    expense_description = None
    expense_date = None
    if not tables:
        raise UnableGetExpenseException
    try:
        if len(tables) <= 2:
            raise UnableGetExpenseException
        expense_description = tables[0].tr.td.get_text()
        expense_value = tables[1].find_all('tr')[0] \
                                 .find_all('td')[1] \
                                 .get_text()
        expense_date = tables[1].find_all('tr')[1] \
                                .find_all('td')[1] \
                                .get_text()
    except (AttributeError, IndexError):
        raise UnableGetExpenseException
    expense.description = utils.remove_spaces(expense_description)
    expense_value = re.sub(r"[$\,]*", "", utils.remove_spaces(expense_value))
    try:
        expense.expense_value = float(expense_value)
    except ValueError:
        raise UnableGetExpenseException
    expense_date = utils.remove_spaces(expense_date)
    try:
        expense.date_expense = datetime.strptime(
            expense_date, '%Y/%m/%d %H:%M:%S'
        )
    except ValueError:
        raise UnableGetExpenseException
    return expense


def get_bancolombia_pse_expense(message_body: str) -> Expense | None:
    """
    Function to return an expense, cleaning the info from Bancolombia
    pse payments
    """
    soup = BeautifulSoup(message_body, 'html.parser')
    raw_tx_value = soup.find(string=re.compile('Valor de la'))
    tx_status = clean_string(str(soup.find(string=re.compile('Estado de'))))
    tx_value = clean_string(str(raw_tx_value))
    date_tx = clean_string(str(soup.find(string=re.compile('Fecha de'))))
    if tx_status.split(':')[1][1:].lower() != 'aprobada':
        return None
    try:
        tx_desc = clean_string(
            str(raw_tx_value.previous_element.previous_element)
        )
    except AttributeError:
        raise UnableGetExpenseException
    try:
        tx_value_clean = tx_value.split(':')[1][1:] \
                                 .replace('.', '') \
                                 .replace(',', '.') \
                                 .replace('$ ', '')
        return Expense(
            expense_value=int(tx_value_clean),
            description=tx_desc,
            date_expense=datetime.strptime(
                date_tx.split(':')[1][1:], '%d/%m/%Y'
            )
        )
    except IndexError:
        raise UnableGetExpenseException


def clean_string(str_to_clean: str):
    return re.sub(r'\s+', ' ', str_to_clean.replace('\n', ' ').strip())
