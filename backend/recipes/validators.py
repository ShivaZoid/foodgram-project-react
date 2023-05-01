from string import hexdigits

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator


def hex_color_validator(color: str) -> str:
    """Проверяет - может ли значение быть шестнадцатеричным цветом.

    Raises:
        ValidationError: Переданное значение не корректной длины.
        ValidationError: Символы значения выходят за пределы 16-ричной системы.
    """

    color = color.strip(' #')
    if len(color) not in (3, 6):
        raise ValidationError(
            f'Код цвета {color} не правильной длины ({len(color)}).'
        )
    if not set(color).issubset(hexdigits):
        raise ValidationError(
            f'{color} не шестнадцатиричное.'
        )
    if len(color) == 3:
        return f'#{color[0] * 2}{color[1] * 2}{color[2] * 2}'.upper()
    return '#' + color.upper()


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
