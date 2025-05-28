from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect, HttpResponseForbidden

def index(request):
    return HttpResponse("<h1>Hello, world!</h1>")


def about(request):
    name = request.GET.get("name", "hjkh")
    return HttpResponse(f"""
                        <h2> О пользователе</h2>
                        <p>Имя: {name}</p>
                        """)


def userInfo(request):
    host = request.META["HTTP_HOST"]
    user_agent = request.META["HTTP_USER_AGENT"]
    path = request.path

    return HttpResponse(f"""
                        <p>Host: {host}</p>
                        <p>User agent: {user_agent}</p>
                        <p>Path: {path}</p>
                        """)


def tasks(request):
    return HttpResponse("<h1>Список задач</h1>")


def task(request):
    return HttpResponse("<h1>Задача</h1>")


def notThis(request):
    return HttpResponseRedirect("/")


def andNotThis(request):
    return HttpResponsePermanentRedirect("/")


def ageAccess(request):
    age = int(request.GET.get("age", 0))
    if (age > 17):
        return HttpResponse("<h1>Welcome</h1>")
    else:
        return HttpResponseForbidden("<h1>not aged</h1>")

