from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

# Create your views here.


async def simple_view(request: HttpRequest) -> HttpResponse:
    return HttpResponse('Hello from "Core" app!')
