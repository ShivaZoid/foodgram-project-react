from django.contrib.auth.models import AbstractUser
from django.db import models

from .validators import validate_username


class User(AbstractUser):
    """Модель для пользователей.

    Attributes:
        username: уникальный юзернейм.
        email: почта пользователя.
        first_name: имя.
        last_name: фамилия.
    """

    username = models.CharField(
        'Уникальный юзернейм',
        max_length=150,
        unique=True,
        validators=(validate_username,),
    )
    email = models.EmailField(
        'Адрес электронной почты',
        max_length=254,
        unique=True,
    )
    first_name = models.CharField(
        'Имя',
        max_length=150,
        blank=True
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=150,
        blank=True
    )
    password = models.CharField(
        'Пароль',
        max_length=128,
    )
    is_active = models.BooleanField(
        'Активирован',
        default=True,
    )

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.username}: {self.email}'


class Subscriptions(models.Model):
    """
    Модель, представляющая подписку пользователя на автора.

    Attributes:
        user: подписчик.
        author: автор, на которого подписывается пользователь.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Автор'
    )
    date_added = models.DateTimeField(
        verbose_name='Дата создания подписки',
        auto_now_add=True,
        editable=False
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
        return (
            f'Пользователь {self.user.username}, автор {self.author.username}'
        )
