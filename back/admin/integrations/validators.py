import re
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

def validate_ID(value):
    pattern = re.compile("^[A-Z0-9_]+$")
    if not pattern.match(value):
        raise ValidationError(
            _("%(value)s should only contain capitals, numbers and/or underscores"),
            params={"value": value},
        )

def validate_status_code(status_code_list):
    pattern = re.compile("^[1-5][1-5][1-5]$")
    for value in status_code_list:
        if not pattern.match(value):
            raise ValidationError(
                _("Not all values are within the range of 100 and 599"),
            )

def validate_continue_if(value):
    if len(value):
        if "response_notation" not in value:
            raise ValidationError(
                _("Continue if must include `response_notation` as a key."),
            )
        if "value" not in value:
            raise ValidationError(
                _("Continue if must include `value` as a key."),
            )

def validate_polling(value):
    if len(value):
        if "interval" not in value:
            raise ValidationError(
                _("Polling must include `interval` as a key."),
            )
        if "amount" not in value:
            raise ValidationError(
                _("Polling must include `amount` as a key."),
            )
