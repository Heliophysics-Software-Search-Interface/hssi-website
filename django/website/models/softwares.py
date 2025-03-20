import uuid
from django.db import models

from .organizations import Organizations
from .persons import Persons
from .ivoa_entries import IvoaEntries
from .functionalities import Functionalities
from .basics import RepoStatuses, OperatingSystems, Keywords, Awards, Images, PhenomenaTypes
from .licenses import Licenses

class ProgrammingLanguages(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    version = models.CharField(max_length=50, blank=True, null=True)
    organization = models.ForeignKey(
        Organizations,
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='programming_languages'
    )

    class Meta: ordering = ['name', 'version']
    def __str__(self): 
        return self.name + (f' {self.version}' if self.version else '')

class FileFormats(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    extension = models.CharField(max_length=25)
    fullName = models.CharField(max_length=100, blank=True, null=True)
    affiliation = models.ForeignKey(
        Organizations,
        on_delete=models.CASCADE,
        null=True, 
        blank=True, 
        related_name='file_formats'
    )

    # specified for intellisense, defined in Softwares model
    softares: models.Manager['Softwares']

    class Meta: ordering = ['extension']
    def __str__(self): 
        return self.extension + (f' - {self.fullName}' if self.fullName else '')
    
class Softwares(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)    
    programmingLanguage = models.ForeignKey(
        ProgrammingLanguages,
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='softwares'
    )
    publicationDate = models.DateField()
    authors = models.ManyToManyField(Persons, related_name='softwares')
    publisher = models.ForeignKey(
        Organizations,
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='softwares'
    )
    relatedInstruments = models.ForeignKey(
        IvoaEntries,
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='softwares'
    )
    relatedObservatories = models.ForeignKey(
        IvoaEntries,
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
    softwareFunctionality = models.ManyToManyField(Functionalities, related_name='softwares')
    documentation = models.URLField(blank=True, null=True)
    dataInputs = models.ManyToManyField(Functionalities, related_name='softwares_data')
    supportedFileFormats = models.ManyToManyField(FileFormats, related_name='softwares')
    relatedPublications = models.TextField(blank=True, null=True)
    relatedDatasets = models.TextField(blank=True, null=True)
    developmentStatus = models.ForeignKey(
        RepoStatuses,
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='softwares'
    )
    operatingSystem = models.ManyToManyField(OperatingSystems, related_name='softwares')
    metadataLicense = models.ForeignKey(
        Licenses,
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='softwares'
    )
    license = models.ForeignKey(
        Licenses,
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='softwares_license'
    )
    relatedRegion = models.TextField(blank=True, null=True)
    keywords = models.ManyToManyField(Keywords, related_name='softwares')
    relatedSoftware = models.TextField(blank=True, null=True)
    interopableSoftware = models.TextField(blank=True, null=True)
    funder = models.ForeignKey(
        Organizations,
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='softwares_funder'
    )
    award = models.ForeignKey(
        Awards,
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='softwares'
    )
    codeRepositoryUrl = models.URLField(blank=True, null=True)
    logo = models.ForeignKey(
        Images,
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='softwares'
    )
    relatedPhenomena = models.ManyToManyField(PhenomenaTypes, related_name='softwares')

    class Meta: ordering = ['softwareName']
    def __str__(self): return self.softwareName