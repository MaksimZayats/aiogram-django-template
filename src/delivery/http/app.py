from django.core.wsgi import get_wsgi_application

from core.configs.infrastructure import configure_infrastructure

configure_infrastructure(service_name="http")
wsgi = get_wsgi_application()
