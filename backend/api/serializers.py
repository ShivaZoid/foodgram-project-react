from collections import OrderedDict

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import F, QuerySet
from django.db.transaction import atomic
from drf_base64.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import Ingredient, Recipe, Tag
from .services import recipe_ingredients_set
from .validators import ingredients_validator, tags_exist_validator


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для использования с моделью User."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name',
            'is_subscribed', 'password',
        )
        extra_kwargs = {'password': {'write_only': True}}
        read_only_fields = 'is_subscribed',

    def get_is_subscribed(self, obj: User):
        """Проверка подписки пользователей."""
        user = self.context.get('request').user

        if user.is_anonymous or (user == obj):
            return False

        return user.subscriptions.filter(author=obj).exists()

    def create(self, validated_data):
        """ Создаёт нового пользователя с запрошенными полями."""
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()

        return user


class ShortRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Recipe.

    Определён укороченный набор полей для некоторых эндпоинтов.
    """

    class Meta:
        model = Recipe
        fields = 'id', 'name', 'image', 'cooking_time'
        read_only_fields = '__all__',


class UserSubscribeSerializer(UserSerializer):
    """
    Сериализатор вывода авторов на которых подписан текущий пользователь.
    """

    recipes = ShortRecipeSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name',
            'is_subscribed', 'recipes',
            'recipes_count',
        )
        read_only_fields = '__all__',

    def get_is_subscribed(*args):
        """
        Проверка подписки пользователей.

        Переопределённый метод родительского класса для уменьшения нагрузки,
        так как в текущей реализации всегда вернёт `True`.
        """
        return True

    def get_recipes_count(self, obj):
        """
        Показывает общее количество рецептов у каждого автора.
        """
        return obj.recipes.count()


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для вывода тэгов."""

    class Meta:
        model = Tag
        fields = '__all__'
        read_only_fields = '__all__',

    def validate(self, data):
        """
        Валидация вводных данных при создании/редактировании тэга.
        """
        for attr, value in data.items():
            data[attr] = value.sttrip(' #').upper()

        return data


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для вывода ингридиентов."""

    class Meta:
        model = Ingredient
        fields = '__all__'
        read_only_fields = '__all__',


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов."""

    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author',
            'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name',
            'image', 'text', 'cooking_time',
        )
        read_only_fields = (
            'is_favorite',
            'is_shopping_cart',
        )

    def get_ingredients(self, recipe: Recipe):
        """Получает список ингридиентов для рецепта."""
        ingredients = recipe.ingredients.values(
            'id', 'name', 'measurement_unit', amount=F('recipe__amount')
        )
        return ingredients

    def get_is_favorited(self, recipe: Recipe):
        """Находится ли рецепт в избранном."""
        user = self.context.get('view').request.user

        if user.is_anonymous:
            return False

        return user.favorites.filter(recipe=recipe).exists()

    def get_is_in_shopping_cart(self, recipe: Recipe):
        """Находится ли рецепт в списке  покупок."""
        user = self.context.get('view').request.user

        if user.is_anonymous:
            return False

        return user.carts.filter(recipe=recipe).exists()

    def validate(self, data: OrderedDict):
        """
        Проверка вводных данных при создании/редактировании рецепта.
        """
        tags_ids: list[int] = self.initial_data.get('tags')
        ingredients = self.initial_data.get('ingredients')

        if not tags_ids or not ingredients:
            raise ValidationError('Недостаточно данных.')

        tags_exist_validator(tags_ids, Tag)
        ingredients = ingredients_validator(ingredients, Ingredient)

        data.update({
            'tags': tags_ids,
            'ingredients': ingredients,
            'author': self.context.get('request').user
        })
        return data

    @atomic
    def create(self, validated_data):
        """Создаёт рецепт.

        Args:
            validated_data (dict): Данные для создания рецепта.

        Returns:
            Recipe: Созданый рецепт.
        """
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        recipe_ingredients_set(recipe, ingredients)
        return recipe

    @atomic
    def update(self, recipe: Recipe, validated_data: dict):
        """Обновляет рецепт."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        for key, value in validated_data.items():
            if hasattr(recipe, key):
                setattr(recipe, key, value)

        if tags:
            recipe.tags.clear()
            recipe.tags.set(tags)

        if ingredients:
            recipe.ingredients.clear()
            recipe_ingredients_set(recipe, ingredients)

        recipe.save()
        return recipe
