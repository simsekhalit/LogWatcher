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
def init_db(request):
	"""Shows details about a log watcher object."""

	Watchers.objects.create(wid=0, name="Best Watcher")
	Watchers.objects.create(wid=1, name="Good Watcher")
	Watchers.objects.create(wid=2, name="Fast Watcher")

	WatcherRules.objects.create(wid=0, path="", rule="")
	WatcherRules.objects.create(wid=1, path="", rule="")
	WatcherRules.objects.create(wid=2, path="", rule="")

	WatcherLogs.objects.create(wid=0, log="")
	WatcherLogs.objects.create(wid=1, log="")
	WatcherLogs.objects.create(wid=2, log="")

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
