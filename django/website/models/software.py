import uuid
from django.db import models

from .organization import Organization
from .person import Person
from .ivoa_entry import IvoaEntry
from .functionality import Functionality
from .basics import RepoStatus, OperatingSystem, Keyword, Award, Image, PhenomenaType
from .license import License
from .submission_info import SubmissionInfo

class ProgrammingLanguage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    version = models.CharField(max_length=50, blank=True, null=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='programming_languages'
    )

    class Meta: ordering = ['name', 'version']
    def __str__(self): 
        return self.name + (f' {self.version}' if self.version else '')

class FileFormat(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    extension = models.CharField(max_length=25)
    fullName = models.CharField(max_length=100, blank=True, null=True)
    affiliation = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True, 
        blank=True, 
        related_name='file_formats'
    )

    # specified for intellisense, defined in Softwares model
    softares: models.Manager['Software']

    class Meta: ordering = ['extension']
    def __str__(self): 
        return self.extension + (f' - {self.fullName}' if self.fullName else '')
    
class Software(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)    
    programmingLanguage = models.ForeignKey(
        ProgrammingLanguage,
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='softwares'
    )
    publicationDate = models.DateField()
    authors = models.ManyToManyField(Person, related_name='softwares')
    publisher = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='softwares'
    )
    relatedInstruments = models.ForeignKey(
        IvoaEntry,
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='softwares'
    )
    relatedObservatories = models.ForeignKey(
        IvoaEntry,
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='observatories'
    )
    softwareName = models.CharField(max_length=150)
    versionNumber = models.CharField(max_length=25, blank=True, null=True)
    versionDate = models.DateField(blank=True, null=True)
    versionDescription = models.TextField(blank=True, null=True)
    versionPid = models.CharField(max_length=200, blank=True, null=True)
    persistentIdentifier = models.CharField(max_length=200, blank=True, null=True)
    referencePublication = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    conciseDescription = models.TextField(max_length=200, blank=True, null=True)
    softwareFunctionality = models.ManyToManyField(Functionality, related_name='softwares')
    documentation = models.URLField(blank=True, null=True)
    dataInputs = models.ManyToManyField(Functionality, related_name='softwares_data')
    supportedFileFormats = models.ManyToManyField(FileFormat, related_name='softwares')
    relatedPublications = models.TextField(blank=True, null=True)
    relatedDatasets = models.TextField(blank=True, null=True)
    developmentStatus = models.IntegerField(choices=RepoStatus.choices, default=RepoStatus.WIP)
    operatingSystem = models.ManyToManyField(OperatingSystem, related_name='softwares')
    metadataLicense = models.ForeignKey(
        License,
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='softwares'
    )
    license = models.ForeignKey(
        License,
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='softwares_license'
    )
    relatedRegion = models.TextField(blank=True, null=True)
    keywords = models.ManyToManyField(Keyword, related_name='softwares')
    relatedSoftware = models.TextField(blank=True, null=True)
    interopableSoftware = models.TextField(blank=True, null=True)
    funder = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='softwares_funder'
    )
    award = models.ForeignKey(
        Award,
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='softwares'
    )
    codeRepositoryUrl = models.URLField(blank=True, null=True)
    logo = models.ForeignKey(
        Image,
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='softwares'
    )
    relatedPhenomena = models.ManyToManyField(PhenomenaType, related_name='softwares')
    submissionInfo = models.ForeignKey(
        SubmissionInfo,
        on_delete=models.CASCADE,
        related_name='softwares'
    )

    class Meta:
        ordering = ['softwareName']
        verbose_name_plural = "  Software"
    def __str__(self): return self.softwareName
