"""
Custom DRF exception handling to return human-friendly codes/messages.
"""
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.views import exception_handler as drf_exception_handler


class DomainError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Нарушено бизнес-правило."
    default_code = "domain_error"


class BusinessRuleError(DomainError):
    default_detail = "Невозможно выполнить операцию."
    default_code = "business_rule"


def custom_exception_handler(exc, context):
    """
    Normalize exceptions into a consistent JSON shape:
    {"code": "...", "message": "...", "details": {...}}
    """
    if isinstance(exc, DjangoValidationError):
        exc = ValidationError(
            detail=getattr(exc, "message_dict", None) or exc.messages,
            code="validation_error",
        )

    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    raw_detail = response.data
    message = None
    code = getattr(getattr(exc, "detail", None), "code", None) or getattr(
        exc, "default_code", "error"
    )

    if isinstance(raw_detail, dict):
        message = raw_detail.get("detail")
    else:
        message = raw_detail

    response.data = {
        "code": code or "error",
        "message": message or "Request failed",
        "details": raw_detail if isinstance(raw_detail, dict) else None,
    }
    return response
