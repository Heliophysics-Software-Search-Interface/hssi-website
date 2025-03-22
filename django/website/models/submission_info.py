import uuid
from django.db import models
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .person import Person, Curator

class SubmissionInfo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dateModified = models.DateField(auto_now=True)
    modificationDescription = models.TextField(blank=True, null=True)
    metadataVersionNumber = models.CharField(max_length=50, blank=True, null=True)
    submitter = models.ForeignKey(
        Person,
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='submission_info'
    )
    submitterEmail = models.EmailField()
    curator = models.ForeignKey(
        Curator,
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='submission_info_owner'
    )
    curatorEmail = models.EmailField()
    submissionDate = models.DateField()
    internalStatusCode = models.IntegerChoices
    internalStatusNote = models.TextField(blank=True, null=True)
    leadCurator = models.ForeignKey(
        Curator,
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='submission_info_leader'
    )
    lastContactDate = models.DateField(blank=True, null=True)
    contactCount = models.IntegerField(default=0)
    curatorLock = models.BooleanField(default=False)
    outOfSync = models.BooleanField(default=False)

    class Meta: ordering = ['submissionDate']
    def __str__(self): return f"{self.submissionDate} - {self.submissionStatus}"

# Definitions for admin page ---------------------------------------------------

class SubmissionInfoResource(resources.ModelResource):
    class Meta: model = SubmissionInfo
class SubmissionInfoAdmin(ImportExportModelAdmin): resource_class = SubmissionInfoResource