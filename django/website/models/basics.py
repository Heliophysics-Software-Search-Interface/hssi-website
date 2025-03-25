import uuid
from django.db import models

class RepoStatus(models.IntegerChoices):
    CONCEPT = 1, "Concept"
    WIP = 2, "WIP"
    SUSPENDED = 3, "Suspended"
    ABANDONED = 4, "Abandoned"
    ACTIVE = 5, "Active"
    INACTIVE = 6, "Inactive"
    UNSUPPORTED = 7, "Unsupported"
    MOVED = 8, "Moved"

class OperatingSystem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)

    class Meta: ordering = ['name']
    def __str__(self): return self.name

class PhenomenaType(models.Model):
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
