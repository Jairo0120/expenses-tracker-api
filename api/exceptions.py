from fastapi import HTTPException
import logging


logger = logging.getLogger("expenses-tracker")


class IntegrityException(HTTPException):
    def __init__(self, status_code, detail, current_val):
        logger.error(f"Integrity error: {detail}")
        errors = []
        for integrity_error in detail:
            field = integrity_error.split(' ')[-1].split('.')[-1]
            field_value = getattr(current_val, field)
            errors.append(
                f"The value {field_value} for the field {field} already exist"
            )
        super().__init__(status_code, errors)
