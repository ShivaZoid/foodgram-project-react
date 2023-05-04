from django.core.management import BaseCommand


class Command(BaseCommand):
    help = 'тест'

    def handle(self):
        self.stdout.write(self.style.SUCCESS('Working!'))
