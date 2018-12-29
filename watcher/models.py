from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class Watchers(models.Model):
	"""Watcher objects table"""
	wid = models.AutoField(primary_key=True)
	name = models.TextField()


class WatcherLogs(models.Model):
	class Meta:
		unique_together = ("wid", "log")
	wid = models.IntegerField()
	log = models.TextField()


class WatcherRules(models.Model):
	"""Table which tracks all LogWatch object tables"""
	class Meta:
		unique_together = ("wid", "rule")
	wid = models.IntegerField()
	rule = models.TextField()
	path = models.TextField()
