import uuid
from django.db import models
from import_export import resources
from import_export.admin import ImportExportModelAdmin

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

# Definitions for admin page ---------------------------------------------------

class OperatingSystemResource(resources.ModelResource):
    class Meta: model = OperatingSystem
class OperatingSystemAdmin(ImportExportModelAdmin): resource_class = OperatingSystemResource

class PhenomenaTypeResource(resources.ModelResource):
    class Meta: model = PhenomenaType
class PhenomenaTypeAdmin(ImportExportModelAdmin): resource_class = PhenomenaTypeResource

class KeywordResource(resources.ModelResource):
    class Meta: model = Keyword
class KeywordAdmin(ImportExportModelAdmin): resource_class = KeywordResource

class AwardResource(resources.ModelResource):
    class Meta: model = Award
class AwardAdmin(ImportExportModelAdmin): resource_class = AwardResource

class ImageResource(resources.ModelResource):
    class Meta: model = Image
class ImageAdmin(ImportExportModelAdmin): resource_class = ImageResource