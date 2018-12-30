from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from watcher.models import Watchers, WatcherLogs, WatcherRules

# Create your views here.


@login_required
def create(request):
	"""Creates a new Watcher instance."""
	return redirect(index)


@login_required
def logs(request, wid=None):
	"""Shows filtered logs of corresponding Watcher instance."""
	return redirect(index)


@login_required
def rules(request, wid=None):
	"""Shows and updates rules of a Watcher instance."""
	return redirect(index)


@login_required
def index(request):
	"""Home page which shows active Watcher instances."""
	watchers = []
	for watcher in Watchers.objects.all():
		_rules = len(WatcherRules.objects.filter(wid=watcher.wid))
		_logs = len(WatcherLogs.objects.filter(wid=watcher.wid))
		watchers.append({"wid": watcher.wid, "name": watcher.name, "rules": _rules, "logs": _logs})
		print(WatcherRules.objects.filter(wid=watcher.wid))

	return render(request, "index.html", {"watchers": watchers})
