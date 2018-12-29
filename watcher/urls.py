from django.urls import path, re_path
import sys
from . import views

urlpatterns = [
    path("", views.index, name='index'),
    path("create/", views.create, name='create'),
    re_path(r"^logs/(?P<wid>[0-9]+)$", views.logs, name='logs'),
    re_path(r"^rules/(?P<wid>[0-9]+)$", views.rules, name='rules'),
    path("init_db/", views.init_db, name="init_db")
]

print("READY", file=sys.stderr)
