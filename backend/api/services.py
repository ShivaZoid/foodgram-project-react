from typing import TYPE_CHECKING

from recipes.models import IngredientInRecipe, Recipe

if TYPE_CHECKING:
    from recipes.models import Ingredient


def recipe_ingredients_set(
    recipe: Recipe,
    ingredients: dict[int, tuple['Ingredient', int]]
) -> None:
    """Записывает ингредиенты вложенные в рецепт.

    Создаёт объект IngredientInRecipe связывающий объекты Recipe и
    Ingredient с указанием количества amount конкретного ингридиента.
    """
    objs = []

    for ingredient, amount in ingredients.values():
        objs.append(IngredientInRecipe(
            recipe=recipe,
            ingredients=ingredient,
            amount=amount
        ))

    IngredientInRecipe.objects.bulk_create(objs)


incorrect_layout = str.maketrans(
    'qwertyuiop[]asdfghjkl;\'zxcvbnm,./',
    'йцукенгшщзхъфывапролджэячсмитьбю.'
)
