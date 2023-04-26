from django.contrib import admin

from .models import (FavoriteRecipe, Ingredient, Recipe,
                     IngredientInRecipe, ShoppingCart, Subscribe, Tag)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Конфигурация отображения данных.

    Attributes:
        list_display: отображаемые поля.
        search_fields: интерфейс для поиска.
        list_filter: возможность фильтрации.
    """

    list_display = ('id', 'name', 'color', 'slug',)
    search_fields = ('name', 'slug',)
    empty_value_display = '-пусто-'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Конфигурация отображения данных.

    Attributes:
        list_display: отображаемые поля.
        search_fields: интерфейс для поиска.
        list_filter: возможность фильтрации.
    """

    list_display = ('id', 'name', 'measurement_unit',)
    search_fields = ('name', 'measurement_unit',)
    list_filter = ('name',)
    empty_value_display = '-пусто-'


class RecipeIngredientAdmin(admin.StackedInline):
    model = IngredientInRecipe
    autocomplete_fields = ('ingredient',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Конфигурация отображения данных.

    Attributes:
        list_display: отображаемые поля.
        search_fields: интерфейс для поиска.
        list_filter: возможность фильтрации.
        inlines: список моделей, связанных с моделью Recipe
        и редактируемых вместе с ней.

    Methods:
        get_tags: возвращает строку со списком тегов, связанных с рецептом.
        get_ingredients: возвращает строку со списком ингредиентов,
        связанных с рецептом и их количеством.
        get_favorite_count: возвращает количество пользователей,
        добавивших рецепт в избранное.
    """

    list_display = (
        'id', 'author', 'name',
        'text', 'get_ingredients', 'get_tags',
        'cooking_time', 'get_favorite_count'
    )
    search_fields = (
        'name', 'cooking_time',
        'author__email', 'ingredients__name'
    )
    list_filter = ('author', 'name', 'tags',)
    inlines = (RecipeIngredientAdmin,)
    empty_value_display = '-пусто-'

    @admin.display(description='Тэги')
    def get_tags(self, obj):
        list_ = [_.name for _ in obj.tags.all()]
        return ', '.join(list_)

    @admin.display(description=' Ингредиенты ')
    def get_ingredients(self, obj):
        return '\n '.join([
            f'{item["ingredient__name"]} - {item["amount"]}'
            f' {item["ingredient__measurement_unit"]}.'
            for item in obj.recipe.values(
                'ingredient__name',
                'amount', 'ingredient__measurement_unit')])

    @admin.display(description='В избранном')
    def get_favorite_count(self, obj):
        return obj.favorite_recipe.count()


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    """Конфигурация отображения данных.

    Attributes:
        list_display: отображаемые поля.
        search_fields: интерфейс для поиска.
        list_filter: возможность фильтрации.
    """

    list_display = ('id', 'user', 'author',)
    search_fields = ('user__email', 'author__email',)
    empty_value_display = '-пусто-'


@admin.register(FavoriteRecipe)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    """Конфигурация отображения данных.

    Attributes:
        list_display: отображаемые поля.

    Methods:
        get_recipe: получение списка названий первых пяти рецептов в избранном.
        get_count: получение количества рецептов в избранном.
    """

    list_display = ('id', 'user', 'get_recipe', 'get_count')
    empty_value_display = '-пусто-'

    @admin.display(description='Рецепты')
    def get_recipe(self, obj):
        return [
            f'{item["name"]} ' for item in obj.recipe.values('name')[:5]]

    @admin.display(description='В избранных')
    def get_count(self, obj):
        return obj.recipe.count()


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Конфигурация отображения данных.

    Attributes:
        list_display: отображаемые поля.

    Methods:
        get_recipe: получение списка названий первых пяти рецептов
        в корзине покупок.
        get_count: получение количества рецептов в корзине покупок.
    """

    list_display = ('id', 'user', 'get_recipe', 'get_count')
    empty_value_display = '-пусто-'

    @admin.display(description='Рецепты')
    def get_recipe(self, obj):
        return [
            f'{item["name"]} ' for item in obj.recipe.values('name')[:5]]

    @admin.display(description='В избранных')
    def get_count(self, obj):
        return obj.recipe.count()
