from django.contrib.auth import get_user_model
from django.core import validators
from django.db import models

from .validators import tag_slug_validator, hex_color_validator


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
        unique=True,
        db_index=False
    )
    slug = models.SlugField(
        'Уникальный слаг',
        max_length=100,
        unique=True,
        validators=(tag_slug_validator,),
        db_index=False
    )

    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        ordering = ('name',)

    def __str__(self):
        return f'{self.name} (цвет: {self.color})'

    def clean(self) -> None:
        self.name = self.name.strip().lower()
        self.slug = self.slug.strip().lower()
        self.color = hex_color_validator(self.color)
        return super().clean()


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
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}.'

    def clean(self) -> None:
        self.name = self.name.lower()
        self.measurement_unit = self.measurement_unit.lower()
        super().clean()


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
        related_name='recipes',
        verbose_name='Автор',
        null=True
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
        verbose_name='Ингредиенты блюда',
        related_name='recipes',
        through='IngredientInRecipe'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления в минутах',
        validators=[
            validators.MinValueValidator(
                1, message='Мин. время приготовления 1 минута'
            ),
        ]
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date', )
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'author'),
                name='unique_for_author',
            ),
        )

    def __str__(self):
        return f'{self.name}. Автор: {self.author}'


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
        verbose_name='В каких рецептах',
        related_name='ingredient',
        on_delete=models.CASCADE
    )
    ingredients = models.ForeignKey(
        Ingredient,
        verbose_name='Связанные ингредиенты',
        related_name='recipe',
        on_delete=models.CASCADE
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
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Количество ингредиентов'
        ordering = ('recipe', )
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='\n%(app_label)s_%(class)s ingredient alredy added\n'
            )
        ]

    def __str__(self) -> str:
        return f'{self.amount} {self.ingredients}'


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
        related_name='favorites',
        verbose_name='Пользователь'
    )
    recipe = models.ManyToManyField(
        Recipe,
        related_name='in_favorites',
        verbose_name='Избранный рецепт'
    )
    date_added = models.DateTimeField(
        verbose_name='Дата добавления',
        auto_now_add=True,
        editable=False
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'user', ),
                name='\n%(app_label)s_%(class)s recipe is favorite alredy\n',
            ),
        )

    def __str__(self) -> str:
        return f'{self.user} -> {self.recipe}'


class ShoppingCart(models.Model):
    """
    Модель корзины покупок пользователя.

    Attributes:
        user: пользователь, которому принадлежит данная корзина покупок.
        recipe: рецепты, которые пользователь добавил в свою корзину покупок.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='carts',
        null=True,
        verbose_name='Владелец списка'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_carts',
        verbose_name='Рецепты в списке покупок'
    )
    date_added = models.DateTimeField(
        verbose_name='Дата добавления',
        auto_now_add=True,
        editable=False
    )

    class Meta:
        verbose_name = 'Покупка'
        verbose_name_plural = 'Покупки'
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'user', ),
                name='\n%(app_label)s_%(class)s recipe is cart alredy\n',
            ),
        )

    def __str__(self) -> str:
        return f'{self.user} -> {self.recipe}'
