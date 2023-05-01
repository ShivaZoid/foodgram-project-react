from typing import Optional

from django.contrib import admin
from django.core.handlers.wsgi import WSGIRequest
from django.utils.html import format_html
from django.utils.safestring import SafeString, mark_safe

from .models import (FavoriteRecipe, Ingredient, Recipe,
                     IngredientInRecipe, ShoppingCart, Tag)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Конфигурация отображения данных.

    Attributes:
        list_display: отображаемые поля.
        search_fields: интерфейс для поиска.
        list_filter: возможность фильтрации.
    """

    list_display = ('name', 'slug', 'color_code')
    search_fields = ('name', 'color',)
    empty_value_display = '-пусто-'

    @admin.display(description='Colored')
    def color_code(self, obj: Tag):
        return format_html(
            '<span style="color: #{};">{}</span>',
            obj.color[1:], obj.color
        )

    color_code.short_description = 'Цветовой код тега'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Конфигурация отображения данных.

    Attributes:
        list_display: отображаемые поля.
        search_fields: интерфейс для поиска.
        list_filter: возможность фильтрации.
    """

    list_display = ('name', 'measurement_unit',)
    search_fields = ('name',)
    list_filter = ('name',)
    empty_value_display = '-пусто-'


class IngredientInline(admin.TabularInline):
    model = IngredientInRecipe
    extra = 2


@admin.register(IngredientInRecipe)
class LinksAdmin(admin.ModelAdmin):
    pass


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Конфигурация отображения данных.

    Attributes:
        list_display: отображаемые поля.
        search_fields: интерфейс для поиска.
        list_filter: возможность фильтрации.
        inlines: список моделей, связанных с моделью Recipe
        и редактируемых вместе с ней.
    """

    list_display = (
        'name',
        'author',
        'get_image',
        'count_favorites',
    )
    search_fields = (
        'name', 'cooking_time',
        'author__email', 'ingredients__name'
    )
    list_filter = ('author', 'name', 'tags',)
    inlines = (IngredientInline,)
    empty_value_display = '-пусто-'

    def get_image(self, obj: Recipe) -> SafeString:
        return mark_safe(f'<img src={obj.image.url} width="80" hieght="30"')

    get_image.short_description = 'Изображение'

    def count_favorites(self, obj: Recipe) -> int:
        return obj.in_favorites.count()

    count_favorites.short_description = 'В избранном'


@admin.register(FavoriteRecipe)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    """Конфигурация отображения данных.

    Attributes:
        list_display: отображаемые поля.
        search_fields: интерфейс для поиска.
    """

    list_display = ('user', 'recipe',)
    search_fields = ('user__username', 'recipe__name')
    empty_value_display = '-пусто-'


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Конфигурация отображения данных.

    Attributes:
        list_display: отображаемые поля.
        search_fields: интерфейс для поиска..
    """

    list_display = ('user', 'recipe',)
    search_fields = ('user__username', 'recipe__name')
    empty_value_display = '-пусто-'
