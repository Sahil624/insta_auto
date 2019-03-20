# Insta Auto

Insta auto is a web based bot written in python (Django). 
Insta auto interacts with instagram over Http requests using requests library in python.
This Repo includes web services modules of Insta auto. We use Django Rest framework for Rest Apis

## Requirements

* pip 3.6 or greater
* python 3.6 or greater
* Redis
* Postgres DB

# Installation

1 Clone this repo

```bash
git clone https://github.com/Sahil624/insta_auto.git
```

2 Make and activate virtual env (Optional)

```bash
python3 -m venv venv
source venv/bin/activate
```

3 Install python packages

```bash
pip install -r requirements.txt
```

3 Install [Redis](https://redis.io/) or use any Redis Cloud Service like [Redis labs](https://redislabs.com/)

4 Install [Postgres Sql](https://www.postgresql.org/) on your machine (Recommended) or use Postgres as a service 
like [Elephant Sql](https://www.elephantsql.com/)

5 Make a config.py file in insta_auto folder as this :-

```python
REDIS_HOST = "[REDIS_HOST]"
REDIS_PASSWORD = "[REDIS_PASSWORD]"
REDIS_PORT = "[REDIS_PORT]"
REDIS_ADDRESS = ("redis://:{}@{}:{}").format(REDIS_PASSWORD, REDIS_HOST, REDIS_PORT)

POSTGRES_URL = "[POSTGRES_URL]"
POSTGRES_PASSWORD = "[POSTGRES_PASSWORD]"
DB_NAME = "[DB_NAME]"
DB_USER = "[DB_USER]"
DB_PORT = "[DB_PORT]"

```

6 Make Django migrations and apply them.
```bash
python manage.py makemigrations accounts users_profile bot
python manage.py migrate
```

7 Start Development server
```bash
python manage.py runserver
```

##### Client Side comming soon...
