from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator


alphanumeric_validator = RegexValidator(
    r'^[-a-zA-Z0-9_]+$',
    'Допускаются только буквенно-цифровые символы и знаки подчеркивания.'
)


def tag_slug_validator(value):
    try:
        alphanumeric_validator(value)
    except ValidationError as exc:
        raise ValidationError(
            'Доступны только буквенно-цифровые символы и знаки подчеркивания.'
        ) from exc
