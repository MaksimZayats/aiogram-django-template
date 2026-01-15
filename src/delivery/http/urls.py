from delivery.http.factories import URLPatternsFactory
from ioc.container import get_container

_container = get_container()
_urlpatterns_factory = _container.resolve(URLPatternsFactory)

urlpatterns = _urlpatterns_factory()
