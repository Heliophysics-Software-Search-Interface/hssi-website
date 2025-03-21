import uuid
from django.db import models

class PhenomenaType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    
    class Meta: ordering = ['name']
    def __str__(self): return self.name

class RepoStatus(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)

    class Meta: ordering = ['name']
    def __str__(self): return self.name

class OperatingSystem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)

    class Meta: ordering = ['name']
    def __str__(self): return self.name

class Keyword(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)

    class Meta: ordering = ['name']
    def __str__(self): return self.name

class Award(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    identifier = models.CharField(max_length=200, blank=True, null=True)

    class Meta: ordering = ['name']
    def __str__(self): return self.name

class Image(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    url = models.URLField(blank=True, null=True)
    description = models.CharField(max_length=250)

    class Meta: ordering = ['description']
    def __str__(self): return self.name