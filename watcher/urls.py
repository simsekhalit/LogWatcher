from django.urls import path, re_path
from . import views

urlpatterns = [
    path("", views.index, name='index'),
    path("create/", views.index, {"create": True}, name="create"),
    re_path(r"^logs/(?P<lwID>[0-9]+)$", views.logs, name='logs'),
    re_path(r"^rules/(?P<lwID>[0-9]+)$", views.rules, name='rules')
]
