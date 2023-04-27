import django.contrib.auth.password_validation as validators
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404
from drf_base64.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (
    Ingredient, IngredientInRecipe, Tag, Recipe, Subscribe
)


User = get_user_model()


class IsSubscribed:

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return user.follower.filter(author=obj).exists()


class UserListSerializer(IsSubscribed,
                         serializers.ModelSerializer):
    """
    Сериализатор списка пользователей с подпиской.
    """

    is_subscribed = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', 'is_subscribed'
        )


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания объектов пользователя.
    """

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username',
            'first_name', 'last_name', 'password',
        )

    def validate_password(self, password):
        validators.validate_password(password)
        return password


class TagSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Tag.
    """

    class Meta:
        model = Tag
        fields = (
            'id', 'name', 'color', 'slug',)


class IngredientSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Ingredient.
    """

    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор ингредиентов в рецепте.
    """
    id = serializers.ReadOnlyField(
        source='ingredient.id'
    )
    name = serializers.ReadOnlyField(
        source='ingredient.name'
    )
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientInRecipe
        fields = (
            'id', 'name',
            'measurement_unit', 'amount'
        )


class IngredientsEditSerializer(serializers.ModelSerializer):
    """
    Сериализатор редактирования ингредиентов.
    """

    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = Ingredient
        fields = ('id', 'amount')


class RecipeUserSerializer(IsSubscribed,
                           serializers.ModelSerializer):
    """
    Сериализатор модели пользователя,
    используемый для вывода информации о пользователе, создавшем рецепт.
    """

    is_subscribed = serializers.SerializerMethodField(
        read_only=True
    )

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', 'is_subscribed'
        )


class RecipeReadSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели рецепта, используемый для вывода информации о рецепте.
    """

    image = Base64ImageField()
    tags = TagSerializer(
        many=True,
        read_only=True
    )
    author = RecipeUserSerializer()
    ingredients = IngredientInRecipeSerializer(
        many=True,
        required=True,
        source='recipe'
    )
    is_favorited = serializers.BooleanField(
        read_only=True
    )
    is_in_shopping_cart = serializers.BooleanField(
        read_only=True
    )

    class Meta:
        model = Recipe
        fields = '__all__'


class RecipeWriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания и редактирования рецепта.
    """

    image = Base64ImageField(
        max_length=None,
        use_url=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    ingredients = IngredientsEditSerializer(
        many=True
    )

    class Meta:
        model = Recipe
        fields = '__all__'
        read_only_fields = ('author',)

    def validate(self, data):
        """
        Проверяет правильность данных, переданных в сериализатор.
        """
        ingredients = data['ingredients']
        ingredient_list = []
        for items in ingredients:
            ingredient = get_object_or_404(
                Ingredient, id=items['id'])
            if ingredient in ingredient_list:
                raise serializers.ValidationError(
                    'Ингредиент должен быть уникальным!'
                )
            ingredient_list.append(ingredient)
        tags = data['tags']
        if not tags:
            raise serializers.ValidationError(
                'Нужен хотя бы один тэг для рецепта!'
            )
        for tag_name in tags:
            if not Tag.objects.filter(name=tag_name).exists():
                raise serializers.ValidationError(
                    f'Тэг {tag_name} не существует!'
                )
        return data

    def validate_cooking_time(self, cooking_time):
        """
        Проверяет, что время приготовления рецепта больше или равно 1.
        """
        if int(cooking_time) < 1:
            raise serializers.ValidationError(
                'Время приготовления рецепта должно быть больше или равно 1!'
            )
        return cooking_time

    def validate_ingredients(self, ingredients):
        """
        Проверяет, что есть минимум 1 ингредиент в рецепте.
        """
        if not ingredients:
            raise serializers.ValidationError(
                'Минимум 1 ингредиент в рецепте!'
            )
        for ingredient in ingredients:
            if int(ingredient.get('amount')) < 1:
                raise serializers.ValidationError(
                    'Количество ингредиента должно быть больше или равно 1!'
                )
        return ingredients

    def create_ingredients(self, ingredients, recipe):
        """
        Создает связанных объектов модели
        """
        for ingredient in ingredients:
            IngredientInRecipeSerializer.objects.create(
                recipe=recipe,
                ingredient_id=ingredient.get('id'),
                amount=ingredient.get('amount'),
            )

    def create(self, validated_data):
        """
        Создание новых объектов модели Recipe.
        """
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        """
        Обновление существующих объектов модели Recipe.
        """
        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
            instance.ingredients.clear()
            self.create_ingredients(ingredients, instance)
        if 'tags' in validated_data:
            instance.tags.set(
                validated_data.pop('tags')
            )
        return super().update(
            instance, validated_data
        )

    def to_representation(self, instance):
        """
        Преобразование в словарь.
        """
        return RecipeReadSerializer(
            instance,
            context={
                'request': self.context.get('request')
            }
        ).data


class SubscribeRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для рецептов, отображаемых в подписках.
    """

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscribeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для подписок.
    """

    id = serializers.IntegerField(source='author.id')
    email = serializers.EmailField(source='author.email')
    username = serializers.CharField(source='author.username')
    first_name = serializers.CharField(source='author.first_name')
    last_name = serializers.CharField(source='author.last_name')
    recipes = serializers.SerializerMethodField()
    is_subscribed = serializers.BooleanField(read_only=True)
    recipes_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Subscribe
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count',
        )

    def get_recipes(self, obj):
        """
        Возвращает список рецептов пользователя, на которого подписаны.
        """
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = (
            obj.author.recipe.all()[:int(limit)] if limit
            else obj.author.recipe.all()
        )
        return SubscribeRecipeSerializer(
            recipes,
            many=True
        ).data


class TokenSerializer(serializers.Serializer):
    """Сериализатор для аутентификации пользователя."""

    email = serializers.CharField(
        label='Email',
        write_only=True
    )
    password = serializers.CharField(
        label='Пароль',
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True
    )
    token = serializers.CharField(
        label='Токен',
        read_only=True
    )

    def validate(self, attrs):
        """
        Проверка введенных данных на валидность.
        Возвращает словарь с данными пользователя,
        иначе генерирует исключение с сообщением об ошибке.
        """
        email = attrs.get('email')
        password = attrs.get('password')
        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                email=email,
                password=password
            )
            if not user:
                raise serializers.ValidationError(
                    'Неверно указаны пользовательские данные.',
                    code='authorization'
                )
        else:
            msg = 'Необходимо указать "электронную почту" и "пароль".'
            raise serializers.ValidationError(
                msg,
                code='authorization'
            )
        attrs['user'] = user
        return


class UserPasswordSerializer(serializers.Serializer):
    """Сериализатор для изменения пароля пользователя."""

    new_password = serializers.CharField(
        label='Новый пароль'
    )
    current_password = serializers.CharField(
        label='Текущий пароль'
    )

    def validate_current_password(self, current_password):
        """Проверяет, что текущий пароль совпадает с переданным."""
        user = self.context['request'].user
        if not authenticate(
                username=user.email,
                password=current_password
                ):
            raise serializers.ValidationError(
                'Неверно указаны пользовательские данные.',
                code='authorization'
            )
        return current_password

    def validate_new_password(self, new_password):
        """Проверет на соответствия определенным критериям"""
        validators.validate_password(new_password)
        return new_password

    def create(self, validated_data):
        """Обновляет пароль пользователя и сохраняет изменения."""
        user = self.context['request'].user
        password = make_password(
            validated_data.get('new_password')
        )
        user.password = password
        user.save()
        return validated_data