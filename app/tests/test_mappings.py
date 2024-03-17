import pytest
from src.cleaning_functions import (
    get_bancolombia_pse_expense, get_itau_cc_expense
)
from src.exceptions import CleaningFunctionNotImplementedException
from src.email_source_mappings import get_cleaning_function


@pytest.mark.parametrize("subject, expected_function", [
    ("Confirmación Transacción PSE", get_bancolombia_pse_expense),
    ("PSE Transacción Aprobada", get_bancolombia_pse_expense),
    ("Notificaciones Itau", get_itau_cc_expense),
])
def test_get_cleaning_function(subject, expected_function):
    """
    Test that the function returns the right function based on the subject
    """
    assert get_cleaning_function(subject) == expected_function


def test_get_cleaning_function_not_implemented():
    """
    Test the function raise an exception when the subject hasn't a mapped
    function
    """
    with pytest.raises(CleaningFunctionNotImplementedException):
        get_cleaning_function("Subject no implemented")
