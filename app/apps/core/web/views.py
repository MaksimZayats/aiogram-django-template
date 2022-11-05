from django.http import HttpRequest, HttpResponse
from django.views import View


class SimpleView(View):
    @staticmethod
    def get(_: HttpRequest) -> HttpResponse:
        return HttpResponse('Hello from "Core" app!')
