import csv

from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify
from django.apps import apps


class Command(BaseCommand):
    help = 'Загрузка из csv файла'

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, help='Путь к файлу')
        parser.add_argument('--model', type=str, help='Имя модели')

    def handle(self, *args, **options):
        path = options.get('path', 'data/ingredients.csv')
        model_name = options.get('model', 'Ingredient')
        Model = apps.get_model('recipes', model_name)
        data = []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    row['slug'] = slugify(row['name'])
                    data.append(Model(**row))
            Model.objects.bulk_create(data)
        except FileNotFoundError as exc:
            raise CommandError(f'Файл не найден: {path}') from exc
        except Exception as error:
            raise CommandError(f'Ошибка: {str(error)}') from error

        self.stdout.write(
            self.style.SUCCESS(f'Все объекты {model_name} загружены!')
        )

# python manage.py load_ingrs --path=foodgram-project-react/data/ingredients.csv --model=Ingredient
