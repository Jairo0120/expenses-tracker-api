from collections.abc import Callable
from .models import Expense
from .exceptions import CleaningFunctionNotImplementedException
from .cleaning_functions import (
    get_bancolombia_pse_expense, get_itau_cc_expense
)


maps = {
    "bancolombia_pse": {
        "function": get_bancolombia_pse_expense,
        "subjects": ["Confirmación Transacción PSE",
                     "PSE Transacción Aprobada"]
    },
    "itau_cc": {
        "function": get_itau_cc_expense,
        "subjects": ["Notificaciones Itau"]
    }
}


def get_all_subjects() -> list:
    return [subject for _, val in maps.items() for subject in val["subjects"]]


def get_cleaning_function(subject: str) -> Callable[[str], Expense]:
    """
    Function that receives an email subject and returns the function
    that can clean the email body of the email that contains that subject
    and that function will return the Expense
    """
    for _, val in maps.items():
        for filter_subject in val['subjects']:
            if filter_subject in subject:
                return val["function"]
    raise CleaningFunctionNotImplementedException
