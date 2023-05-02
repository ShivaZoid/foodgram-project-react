from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Модель для пользователей.

    Attributes:
        email: почта пользователя.
        first_name: имя.
        last_name: фамилия.
    """

    email = models.EmailField(
        'Email',
        max_length=200,
        unique=True,)
    first_name = models.CharField(
        'Имя',
        max_length=150)
    last_name = models.CharField(
        'Фамилия',
        max_length=150)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('id',)

    def __str__(self):
        return self.email
