from rest_framework.pagination import PageNumberPagination


class LimitPageNumberPagination(PageNumberPagination):
    """Пагинация по номеру страницы с лимитом в 6 элементов на странице."""

    page_size = 6
    page_size_query_param = 'limit'
