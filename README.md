[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)


# Aiogram-Django Template

## Features

1. [Custom and configurable](app/config/__app_template__) `app` template
2. [Fully typed](https://github.com/typeddjango/django-stubs) `Django`
3. Async ORM (`Django 4.1+`)
4. [aiogram3](https://docs.aiogram.dev/en/dev-3.x/) as Telegram Bot API
5. [pre-commit hooks](.pre-commit-config.yaml) for code formatting and linting

## Installation

1. #### Clone the Template:
   * `git clone https://github.com/MaximZayats/aiogram-django-template`

2. #### Install Requirements
   * `pip install -r requirements.txt`
   * `pip install -r requirements-dev.txt`

3. #### Change the configuration:
   * Copy `.env.dist`
   * Rename it to `.env`
   * Insert your values

4. #### Make migrations:
   * `make makemigrations` or `python manage.py makemigrations`
   * `make migrate` or `python manage.py migrate`

5. #### Run bot:
   * `make run-bot` or ```python -m app.delivery.bot```

6. #### Run server (Django):
   * Collect static: `python manage.py collectstatic`
   * Run server (local): `make run-local-server` or `python -m uvicorn app.delivery.web.asgi:application`
   * Run server (prod): `make run-prod-server`

7. #### Run app _(Bot + Server)_:
   * `make -j3 run-bot run-local-server`


## Usage

1. #### Create new app
   * `python manage.py startapp APP_NAME`
      * Apps are created using a template: [`app/config/__app_template__`](app/config/__app_template__)
      * You can use your template: `python manage.py startapp APP_NAME --template TEMPLATE_PATH`
      * Or without template: `python manage.py startapp APP_NAME --no-template`

2. #### Register app
   * Register app in [`app/config/application.py`](app/config/application.py)

3. #### Check your apps
   * Run bot
   * Type `/apps`:
      * You should get a list of all your apps
   * Type `/APP_NAME`:
      * You should get a message from your app
