import io

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db.models.aggregates import Count, Sum
from django.db.models.expressions import Exists, OuterRef, Value
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from rest_framework import generics, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action, api_view
from rest_framework.permissions import (SAFE_METHODS, AllowAny,
                                        IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.permissions import IsAdminOrReadOnly
from recipes.models import (FavoriteRecipe, Ingredient, Recipe, ShoppingCart,
                            Subscribe, Tag)
from .serializers import (IngredientSerializer, RecipeReadSerializer,
                          RecipeWriteSerializer, SubscribeRecipeSerializer,
                          SubscribeSerializer, TagSerializer, TokenSerializer,
                          UserCreateSerializer, UserListSerializer,
                          UserPasswordSerializer)


User = get_user_model()


class GetObjectMixin:
    """
    Миксин для получения объекта рецепта по переданному id в запросе.
    """

    serializer_class = SubscribeRecipeSerializer
    permission_classes = (AllowAny,)
    model_class = None
    param_name = None

    def get_object(self):
        obj_id = self.kwargs[self.param_name]
        model = get_object_or_404(self.model_class, id=obj_id)
        self.check_object_permissions(self.request, model)
        return model


class UsersViewSet(UserViewSet):
    """Управление пользователями."""

    serializer_class = UserListSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return User.objects.annotate(
            is_subscribed=Exists(
                self.request.user.follower.filter(
                    author=OuterRef('id'))
            )).prefetch_related(
                'follower', 'following'
        ) if self.request.user.is_authenticated else User.objects.annotate(
            is_subscribed=Value(False))

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от типа запроса."""
        if self.request.method.lower() == 'post':
            return UserCreateSerializer
        return UserListSerializer

    def perform_create(self, serializer):
        """Создание нового пользователя с хэшированным паролем."""
        password = make_password(self.request.data['password'])
        serializer.save(password=password)

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        """Получение списка подписок текущего пользователя."""
        user = request.user
        queryset = Subscribe.objects.filter(user=user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscribeSerializer(
            pages, many=True,
            context={'request': request})
        return self.get_paginated_response(serializer.data)


class TagsViewSet(viewsets.ModelViewSet):
    """Просмотр и редактирование списка тегов."""

    queryset = Tag.objects.all()
    pagination_class = None
    serializer_class = TagSerializer
    permission_classes = (IsAdminOrReadOnly,)


class IngredientsViewSet(viewsets.ModelViewSet):
    """Просмотр и редактирование списка ингредиентов."""

    queryset = Ingredient.objects.all()
    pagination_class = None
    serializer_class = IngredientSerializer
    filterset_class = IngredientFilter
    permission_classes = (IsAdminOrReadOnly,)


class RecipesViewSet(viewsets.ModelViewSet):
    """Работа с рецептами."""

    queryset = Recipe.objects.all()
    filterset_class = RecipeFilter
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от типа запроса."""
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def get_queryset(self):
        """
        QuerySet с аннотациями и
        предварительно загруженными объектами.
        """
        return Recipe.objects.annotate(
            is_favorited=Exists(
                FavoriteRecipe.objects.filter(
                    user=self.request.user, recipe=OuterRef('id'))),
            is_in_shopping_cart=Exists(
                ShoppingCart.objects.filter(
                    user=self.request.user,
                    recipe=OuterRef('id')))
        ).select_related('author').prefetch_related(
            'tags', 'ingredients', 'recipe',
            'shopping_cart', 'favorite_recipe'
        ) if self.request.user.is_authenticated else Recipe.objects.annotate(
            is_in_shopping_cart=Value(False),
            is_favorited=Value(False),
        ).select_related('author').prefetch_related(
            'tags', 'ingredients', 'recipe',
            'shopping_cart', 'favorite_recipe')

    def perform_create(self, serializer):
        """Сохранение объекта."""
        serializer.save(author=self.request.user)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        """
        Создает PDF-файл со списком покупок для авторизованного пользователя.
        """

        buffer = io.BytesIO()
        page = canvas.Canvas(buffer)
        pdfmetrics.registerFont(TTFont('ArialUnicodeMS', 'ARIALUNI.TTF'))
        x_position, y_position = 50, 800
        shopping_cart = (
            Recipe
            .objects
            .filter(shopping_cart__user=request.user)
            .values(
                'ingredients__name',
                'ingredients__measurement_unit'
            )
            .annotate(amount=Sum('recipe__amount')).order_by()
        )
        page.setFont('ArialUnicodeMS', 14)
        if shopping_cart:
            indent = 20
            page.drawString(x_position, y_position, 'Cписок покупок:')
            for index, recipe in enumerate(shopping_cart, start=1):
                page.drawString(
                    x_position, y_position - indent,
                    f'{index}. {recipe["ingredients__name"]} - '
                    f'{recipe["amount"]} '
                    f'{recipe["ingredients__measurement_unit"]}.'
                )
                y_position -= 15
                if y_position <= 50:
                    page.showPage()
                    y_position = 800
            page.save()
            buffer.seek(0)
            return FileResponse(
                buffer,
                as_attachment=True,
                filename='shoppingcart.pdf'
            )
        page.setFont('ArialUnicodeMS', 24)
        page.drawString(
            x_position,
            y_position,
            'Cписок покупок пуст!'
        )
        page.save()
        buffer.seek(0)
        return FileResponse(
            buffer,
            as_attachment=True,
            filename='shoppingcart.pdf'
        )


class AddAndDeleteSubscribe(generics.RetrieveDestroyAPIView,
                            generics.ListCreateAPIView):
    """Подписка и отписка от пользователя."""

    serializer_class = SubscribeSerializer

    def get_queryset(self):
        """Информация о всех подписках пользователя."""
        return self.request.user.follower.select_related(
            'following'
        ).prefetch_related(
            'following__recipe'
        ).annotate(
            recipes_count=Count('following__recipe'),
            is_subscribed=Value(True), )

    def get_object(self):
        """
        Возвращает пользователя, на которого осуществляется подписка/отписка.
        """
        user_id = self.kwargs['user_id']
        user = get_object_or_404(User, id=user_id)
        self.check_object_permissions(self.request, user)
        return user

    def create(self, request, *args, **kwargs):
        """
        Создает новую подписку на указанного пользователя
        и возвращает сериализованные данные созданной подписки.
        """
        instance = self.get_object()
        if request.user.id == instance.id:
            return Response(
                {'errors': 'На самого себя не подписаться!'},
                status=status.HTTP_400_BAD_REQUEST)
        if request.user.follower.filter(author=instance).exists():
            return Response(
                {'errors': 'Уже подписан!'},
                status=status.HTTP_400_BAD_REQUEST)
        subs = request.user.follower.create(author=instance)
        serializer = self.get_serializer(subs)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        """
        Удаляет существующую подписку на пользователя.
        """
        self.request.user.follower.filter(author=instance).delete()


class AddDeleteFavoriteRecipe(GetObjectMixin,
                              generics.RetrieveDestroyAPIView,
                              generics.ListCreateAPIView):
    """
    Позволяет добавить или удалить рецепты в избранном у пользователя.
    """

    model_class = Recipe
    param_name = 'recipe_id'

    def create(self, request, *args, **kwargs):
        instance = self.get_object()
        FavoriteRecipe.objects.create(user=request.user, recipe=instance)
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        FavoriteRecipe.objects.filter(
            user=self.request.user,
            recipe=instance
        ).delete()


class AddDeleteShoppingCart(GetObjectMixin,
                            generics.RetrieveDestroyAPIView,
                            generics.ListCreateAPIView):
    """
    Позволяет добавить или удалить рецепт в списоке покупок пользователя.
    """

    model_class = Recipe
    param_name = 'recipe_id'

    def create(self, request, *args, **kwargs):
        instance = self.get_object()
        ShoppingCart.objects.create(user=request.user, recipe=instance)
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        ShoppingCart.objects.filter(
            user=self.request.user,
            recipe=instance
        ).delete()


class AuthToken(ObtainAuthToken):
    """Авторизация пользователя."""

    serializer_class = TokenSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        """
        Проверка данных пользователя помощью сериализатора,
        создание токена, при отсутствии, и его возвращении.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response(
            {'auth_token': token.key},
            status=status.HTTP_201_CREATED)


@api_view(['post'])
def set_password(request):
    """
    Позволяет изменить пароль текущего пользователя.

    Требуется передать в запросе текущий и новый пароль.
    Возвращает сообщение об успешном изменении или ошибку валидации.
    """

    serializer = UserPasswordSerializer(
        data=request.data,
        context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(
            {'message': 'Пароль изменен!'},
            status=status.HTTP_201_CREATED)
    return Response(
        {'error': 'Введите верные данные!'},
        status=status.HTTP_400_BAD_REQUEST)
