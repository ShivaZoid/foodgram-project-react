import json

from django.conf import settings
from django.core.management import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загрузка из JSON файла'

    def handle(self, *args, **kwargs):
        data_path = settings.BASE_DIR
        with open(
            f'{data_path}/data/ingredients.json',
            'r',
            encoding='utf-8'
        ) as file:
            data = json.load(file)
            Ingredient.objects.bulk_create(
                Ingredient(**item) for item in data)
        self.stdout.write(self.style.SUCCESS('Все ингридиенты загружены!'))
