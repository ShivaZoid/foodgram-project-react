from enum import Enum, IntEnum


class Tuples(tuple, Enum):
    RECIPE_IMAGE_SIZE = 500, 300
    SYMBOL_TRUE_SEARCH = '1', 'true'
    SYMBOL_FALSE_SEARCH = '0', 'false'
    ADD_METHODS = 'GET', 'POST'
    DEL_METHODS = 'DELETE',
    ACTION_METHODS = 'GET', 'POST', 'DELETE'
    UPDATE_METHODS = 'PUT', 'PATCH'


class UrlQueries(str, Enum):
    SEARCH_ING_NAME = 'name'
    FAVORITE = 'is_favorited'
    SHOP_CART = 'is_in_shopping_cart'
    AUTHOR = 'author'
    TAGS = 'tags'