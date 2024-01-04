# Aiogram & Django API Template
## Based on [Django API Template](https://github.com/MaksimZayats/python-django-template)

---

## Table of Contents
- [Feature Highlights](#feature-highlights)
- [Configuration Guide](#configuration-guide)
- [Additional Notes](#additional-notes)
- [Quick Start Guide](#quick-start-guide)
   - [Setting Up Locally](#setting-up-locally)
   - [Setting Up with Docker](#setting-up-with-docker)

---

## Feature Highlights

This Django API Template is designed to be robust, scalable, and secure, with features that cater to modern application development needs. Here's an overview of the advanced features and how they benefit your project:

- **[Docker & Docker Compose Integration](https://docs.docker.com/compose/)**: Easily set up and scale your application using Docker containers, ensuring consistent environments across development and production.

- **[Celery](https://docs.celeryq.dev/en/stable/django/first-steps-with-django.html) with [RabbitMQ](https://rabbitmq.com/) and [Redis](https://redis.io/)**: Leverage Celery for asynchronous task processing, using RabbitMQ as a message broker and Redis as a backend for storing results.

- **[Sentry for Error Tracking](https://sentry.io/)**: Integrate with Sentry for real-time error tracking and monitoring, helping you identify and fix issues rapidly.

- **[Django Rest Framework (DRF)](https://www.django-rest-framework.org/)**: Use Django Rest Framework for building RESTful APIs, with support for authentication, serialization, and more.
   - **[DRF Spectacular for OpenAPI](https://drf-spectacular.readthedocs.io/)**: Use DRF Spectacular for OpenAPI documentation, with support for customizing the schema and UI.
   - **[DRF Simple JWT for Authentication](https://django-rest-framework-simplejwt.readthedocs.io/)**: Use DRF Simple JWT for JSON Web Token authentication, with support for customizing token claims and expiration.

- **[Django CORS Headers](https://pypi.org/project/django-cors-headers/)**: Use Django CORS Headers for handling Cross-Origin Resource Sharing (CORS) headers, with support for customizing origins.

- **[Django Silk for Profiling](https://pypi.org/project/django-silk/)**: Utilize Django Silk for profiling and monitoring Django applications, offering insights into performance and optimization.

- **[Django Axes for Security](https://django-axes.readthedocs.io/)**: Use Django Axes for security, with support for blocking brute force attacks and monitoring login attempts.

- **[AWS S3 Integration](https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html)**: Option to use Amazon S3 for static and media file storage, enhancing scalability and performance.

- **Scalability Options**: Configure workers and threads to optimize performance under different load conditions.

- **Up-to-Date Dependencies**: All dependencies are up-to-date as of the latest release. Thanks to [Dependabot](https://dependabot.com/).

---

## Configuration Guide

The `.env` file is a central place to manage environment variables. It's pre-configured to work with Docker Compose out of the box, without any changes required for initial setup. However, for production deployment, certain secrets must be updated for security reasons.

1. **Secrets**:
   - **PostgreSQL, RabbitMQ, Django Secrets**: These are critical for the security of your application. Ensure to replace the placeholder values with strong, unique passwords.

2. **Ports**:
   - **API Port and RabbitMQ Dashboard Port**: Set these ports according to your infrastructure needs. They are exposed to the host machine.

3. **Performance Tuning**:
   - **Workers and Threads**: Adjust these values based on your server's capacity and expected load.

4. **Application Settings**:
   - **Host and Environment**: Set these to match your deployment environment.
   - **Debug and Logging**: Control debug mode and log levels. Set `DJANGO_DEBUG` to `false` in production.
   - **Localization**: Configure `LANGUAGE_CODE` and `TIME_ZONE` as per your requirements.

5. **CORS and CSRF Settings**:
   - Configure these settings to enhance the security of your application by specifying trusted origins.

6. **Database Configuration**:
   - **Postgres Connection**: Set up the database connection using the `DATABASE_URL` variable.

---

## Additional Notes
- **Security**: Always prioritize security, especially when handling environment variables and secrets.
- **Scalability**: Adjust the Docker and Celery configurations as your application scales.
- **Monitoring**: Regularly monitor the performance and health of your application using integrated tools like Sentry and Silk.

By following this guide and utilizing the advanced features, you'll be able to set up a powerful, efficient, and secure Django API environment. Happy coding!

---

## Quick Start Guide

### Setting Up Locally

#### 1. Repository Initialization
   - **Clone the Repository**

#### 2. Environment Setup
   - **Create a Virtual Environment**:
     ```bash
     python3.12 -m venv .venv
     ```
   - **Activate the Virtual Environment**:
     ```bash
     source .venv/bin/activate
     ```

#### 3. Configuration
   - **Environment Variables**:
     - Copy the example environment file:
       ```bash
       cp .env.example .env
       ```
     - _Note: The API can operate without this step, but configuring the environment variables is recommended for full functionality._

#### 4. Dependency Management
   - **Install Dependencies**:
     ```bash
     pip install -r requirements-dev.txt
     ```

#### 5. Database Setup
   - **Run Migrations**:
     ```bash
     make migrate
     ```

#### 6. Launching the Server
   - **Start the Local Server**:
     ```bash
     make run.server.local
     ```

#### 7. Launching the bot
   - **Start the bot**:
     ```bash
     make run.bot.local
     ```

### Setting Up with Docker

#### 1. Repository Initialization
   - **Clone the Repository**

#### 2. Configuration
   - Follow the steps in the [Configuration Guide](#configuration-guide) to set up the `.env` file.

#### 3. Docker Compose
   - **Run Docker Compose**:
     ```bash
     docker compose up -d
     ```
