# Для Ревью(сервер вкл): ip сервера < 130.193.40.223 >, superuser - login: < b@mail.ru >, password: < bzm >

# Продуктовый помощник Foodgram

## Описание
Приложение, на котором пользователи публикуют рецепты кулинарных изделий, подписываться на публикации других авторов и добавлять рецепты в свое избранное.

### Как запустить проект (локально, потребуется Docker):
Клонируем репозиторий и переходим в него:
~~~
cd foodgram-project-react
cd backend
~~~

Предварительно из /backend и /frontend загрузим данные на DockerHub:
~~~
docker login -u ваш никнейм

sudo docker build -t ваш никнейм/foodgram_backend:latest .
docker push ваш никнейм/foodgram_backend:latest

cd ..
cd frontend
docker build -t ваш никнейм/foodgram_frontend:latest .
docker push ваш никнейм/foodgram_frontend:latest
~~~

Так же, создаем файл .env в директории infra:
~~~
cd infra
touch .env

# Заполнем секреты .env
DB_ENGINE='django.db.backends.postgresql'
POSTGRES_DB='foodgram_db'
POSTGRES_USER='foodgram_user'
POSTGRES_PASSWORD='foodgram_u_password'
DB_HOST='db'
DB_PORT='5432'
SECRET_KEY='key'
ALLOWED_HOSTS='127.0.0.1, localhost'
CSRF_TRUSTED_ORIGINS='http://127.0.0.1, http://localhost'
~~~

Далее выполняем команду:
~~~
sudo docker-compose up -d --build
~~~

Для доступа к контейнеру выполняем следующие команды:
~~~
sudo docker-compose exec backend python manage.py makemigrations
~~~
~~~
sudo docker-compose exec backend python manage.py migrate --noinput
~~~
~~~
sudo docker-compose exec backend python manage.py createsuperuser
~~~
~~~
sudo docker-compose exec backend python manage.py collectstatic --no-input
~~~

Дополнительно можно наполнить DB ингредиентами и тэгами:
~~~
sudo docker-compose exec backend python manage.py load_tags
~~~
~~~
sudo docker-compose exec backend python manage.py load_ingrs_json
~~~

Остановить:
~~~
sudo docker-compose stop
~~~

Удалить:
~~~
sudo docker-compose down -v
~~~

## Использование CI/CD

Добавьте в Secrets GitHub Actions переменные окружения для работы базы данных:
~~~
# Server
HOST - ip сервера
USER - login
PASSPHRASE
SSH_KEY - cat ~/.ssh/id_rsa

# Docker Hub:
DOCKER_USERNAME
DOCKER_PASSWORD

# Database
DB_ENGINE
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD
DB_HOST
DB_PORT

# Settings
SECRET_KEY
ALLOWED_HOSTS
CSRF_TRUSTED_ORIGINS

# Telegram
TELEGRAM_TO - ваш telegram_id
TELEGRAM_TOKEN - токен бота
~~~

## На сервере:

### Подготовьте сервер

Войдите на свой удаленный сервер

Остановите службу nginx:
~~~
 sudo systemctl stop nginx
~~~

Установите docker:
~~~
sudo apt install docker.io
~~~

Установите docker-compose:
~~~
sudo curl -SL https://github.com/docker/compose/releases/download/v2.17.2/docker-compose-linux-x86_64 -o /usr/local/bin/docker-compose
~~~

Затем необходимо задать правильные разрешения, чтобы сделать команду docker-compose исполняемой:
~~~
sudo chmod +x /usr/local/bin/docker-compose
~~~

Чтобы проверить успешность установки, запустите следующую команду:
~~~
sudo docker-compose --version
~~~

Cоздаем папку /infra в домашней директории /home/username/:
~~~
cd ~
mkdir infra
~~~

~~~
cd infra
~~~
Скопируйте файлы docker-compose.yaml и nginx/default.conf из вашего проекта на сервер в home/<ваш_username>/infra/docker-compose.yaml
и
home/<ваш_username>/infra/nginx/default.conf соответственно.

Выполняем миграции:
~~~
sudo docker-compose exec backend python manage.py makemigrations
~~~
~~~
sudo docker-compose exec backend python manage.py migrate --noinput
~~~

Србираем статику:
~~~
sudo docker-compose exec backend python manage.py collectstatic --no-input
~~~

Создаем суперюзера:
~~~
sudo docker-compose exec backend python manage.py createsuperuser
~~~

Наполняем DB ингредиентами и тэгами:
~~~
sudo docker-compose exec backend python manage.py load_tags
~~~
~~~
sudo docker-compose exec backend python manage.py load_ingrs_json
~~~

Настройка завершена

---
Документация доступна по эндпойнту: http:// < ip сервера > /redoc/