from re import match

from .exceptions import NotValidUserName


def validate_username(value):
    if value.lower() == 'me':
        raise NotValidUserName(
            ('Использовать имя "me" в качестве username запрещено')
        )
    if match(r'^[\w.@+-]+', value) is None:
        raise NotValidUserName('Не корректный username')
