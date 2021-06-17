# Aiogram-Django Template

## Installation

#### 1. Clone the Template:
   * `git clone https://github.com/MaximZayats/aiogram-django-template`

#### 2. Install Requirements 
   * `pip install -r requirements.txt`
   * `pip install git+https://github.com/MaximZayats/orm_converter`

#### 3. Change Config:
   * Go to the `application/config/`
   * Rename `.env.dist` to `.env`
   * Insert your values

#### 3. Make migrations:
   * Go to the `application/`
   * Run `python manage.py makemigrations`
   * Run `python manage.py migrate`
   
#### 4. Run bot:
   * Go to the `application/`
   * Run bot: `python bot.py`   

#### 5. Run server (Django):
   * Go to the `application/`
   * Collect static: `python manage.py collectstatic`
   * Run server: `uvicorn server:app`
   * Or `python manage.py runserver --e` (emulate the command)


## Usage

#### 1. Create new app
   * `python manage.py startapp APP_NAME`
      * Apps are created using a template: `application/config/app_template`
      * You can use your template: `python manage.py startapp APP_NAME --template TEMPLATE_PATH`
   
#### 2. Register app
   * Import and Add app to `INSTALLED_APPS` in `config/apps.py`
   * Register (include) app urls in `config/web/urls.py`   

#### 3. Check your app
   * Run bot
   * Type `/apps`:
      * You should get a list of all your apps
   * Type `/APP_NAME`:
      * You should get a message from your app
