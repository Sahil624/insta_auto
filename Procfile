release: python manage.py makemigrations accounts users_profile bot
release: python manage.py migrate
worker: python manage.py run_bot_manager
web: daphne insta_auto.asgi:application --port $PORT --bind 0.0.0.0