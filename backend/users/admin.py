from django.contrib import admin
from django.contrib.auth import get_user_model

from users.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Конфигурация отображения данных.

    Attributes:
        list_display: отображаемые поля.
        search_fields: интерфейс для поиска.
        list_filter: возможность фильтрации.
    """

    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
    )
    search_fields = ('email', 'username',)
    list_filter = ('email', 'first_name',)
    empty_value_display = '-пусто-'
