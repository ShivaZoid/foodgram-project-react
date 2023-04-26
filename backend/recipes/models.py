from django.contrib.auth import get_user_model
from django.core import validators
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from .validators import tag_slug_validator


User = get_user_model()


class Tag(models.Model):
    """
    Модель для тегов.

    Attributes:
        name: название
        color: цвет в HEX.
        slug: уникальный слаг.
    """

    name = models.CharField(
        'Название',
        max_length=200,
        unique=True
    )
    color = models.CharField(
        'Цвет в HEX',
        max_length=7,
        unique=True
    )
    slug = models.SlugField(
        'Уникальный слаг',
        max_length=100,
        unique=True,
        validators=(tag_slug_validator,),
    )

    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        ordering = ['-id']

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """
    Модель для ингредиентов.

    Attributes:
        name: название ингредиента.
        measurement_unit: единица измерения ингредиента.
    """

    name = models.CharField(
        'Название ингредиента',
        max_length=200
    )
    measurement_unit = models.CharField(
        'Единица измерения ингредиента',
        max_length=200
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}.'


class Recipe(models.Model):
    """
    Модель для рецептов.

    Attributes:
        author: автор публикации.
        name: название рецепта.
        image: изображение рецепта
        text: текстовое описание
        ingredients: ингредиенты
        tags: теги
        cooking_time: время приготовления в минутах
    """

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipe',
        verbose_name='Автор'
    )
    name = models.CharField(
        'Название рецепта',
        max_length=255
    )
    image = models.ImageField(
        'Изображение рецепта',
        upload_to='static/recipe/',
        blank=True,
        null=True
    )
    text = models.TextField(
        'Описание рецепта'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления в минутах',
        validators=validators.MinValueValidator(
            1, message='Мин. время приготовления 1 минута'
        ),
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date', )

    def __str__(self):
        return f'{self.author}, {self.name}'


class IngredientInRecipe(models.Model):
    """
    Модель, представляющая количество ингредиента, используемого в рецепте.

    Attributes:
        recipe: ссылка на модель Recipe,
        к которой принадлежит данное количество ингредиента.

        ingredient: ссылка на модель Ingredient,
        которая используется в данном количестве ингредиента.

        amount: количество ингредиента, используемого в рецепте.
    """

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient'
    )
    amount = models.PositiveSmallIntegerField(
        default=1,
        verbose_name='Количество',
        validators=(
            validators.MinValueValidator(
                1, message='Мин. количество ингридиентов 1'
            ),
        ),
    )

    class Meta:
        verbose_name = 'Количество ингредиента'
        verbose_name_plural = 'Количество ингредиентов'
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique ingredient'
            )
        ]


class Subscribe(models.Model):
    """
    Модель, представляющая подписку пользователя на автора.

    Attributes:
        user: подписчик.
        author: автор, на которого подписывается пользователь.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription'
            )
        ]

    def __str__(self):
        return f'Пользователь {self.user}, автор {self.author}'


class FavoriteRecipe(models.Model):
    """
    Модель, представляющая избранный рецепт для пользователя.

    Attributes:
        user: пользователь.
        recipe: избранный рецепт.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        related_name='favorite_recipe',
        verbose_name='Пользователь'
    )
    recipe = models.ManyToManyField(
        Recipe,
        related_name='favorite_recipe',
        verbose_name='Избранный рецепт'
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'

    def __str__(self):
        recipe_list = [item['name'] for item in self.recipe.values('name')]
        return f'Пользователь {self.user} добавил {recipe_list} в избранные.'

    @receiver(post_save, sender=User)
    def create_favorite_recipe(sender, instance, created, **kwargs):
        """
        Функция, которая создаёт экземпляр модели FavoriteRecipe
        для пользователя, когда создаётся экземпляр модели User.
        """
        if created:
            return FavoriteRecipe.objects.create(user=instance)


class ShoppingCart(models.Model):
    """
    Модель корзины покупок пользователя.

    Attributes:
        user: пользователь, которому принадлежит данная корзина покупок.
        recipe: рецепты, которые пользователь добавил в свою корзину покупок.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        null=True,
        verbose_name='Пользователь'
    )
    recipe = models.ManyToManyField(
        Recipe,
        related_name='shopping_cart',
        verbose_name='Покупка'
    )

    class Meta:
        verbose_name = 'Покупка'
        verbose_name_plural = 'Покупки'
        ordering = ['-id']

    def __str__(self):
        recipe_list = [item['name'] for item in self.recipe.values('name')]
        return f'Пользователь {self.user} добавил {recipe_list} в покупки.'

    @receiver(post_save, sender=User)
    def create_shopping_cart(sender, instance, created, **kwargs):
        """
        Функция, которая создаёт экземпляр модели ShoppingCart
        для пользователя, когда создаётся экземпляр модели User.
        """
        if created:
            return ShoppingCart.objects.create(user=instance)
