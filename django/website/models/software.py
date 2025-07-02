import uuid
from typing import Callable

from django.db import models
from django.core.exceptions import ObjectDoesNotExist

from .people import Person
from .auxillary_info import Functionality, RelatedItem, Award
from .submission_info import SubmissionInfo
from .roots import ( LEN_NAME, HssiModel,
    RepoStatus, OperatingSystem, Keyword, Image, Phenomena, Organization, 
    License, InstrumentObservatory, ProgrammingLanguage, FileFormat, 
    Region, DataInput
)

class SoftwareVersion(HssiModel):
    '''A snapshot of the software metadata whenever it's updated to a new version'''
    number = models.CharField(max_length=LEN_NAME)
    release_date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    version_pid = models.URLField(blank=True, null=True)
    software: models.ForeignKey['Software'] = models.ForeignKey(
        'Software',
        on_delete=models.CASCADE,
        blank=True, null=True,
        related_name='versions'
    )
    
    # specified for intellisense, defined in Software model
    software_current: models.Manager['Software']

    @classmethod
    def get_top_field(cls) -> models.Field: return cls._meta.get_field("number")

    class Meta: ordering = ['number']
    def __str__(self): return self.number

class Software(HssiModel):
    programmingLanguage = models.ForeignKey(
        ProgrammingLanguage,
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='softwares'
    )
    publicationDate = models.DateField(null=True)
    publisher = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='softwares_published'
    )
    authors = models.ManyToManyField(Person, related_name='softwares')
    relatedInstruments = models.ManyToManyField(
        InstrumentObservatory,
        blank=True, 
        related_name='softwares'
    )
    relatedObservatories = models.ManyToManyField(
        InstrumentObservatory,
        blank=True, 
        related_name='observatories'
    )
    softwareName = models.CharField(max_length=LEN_NAME)
    version = models.OneToOneField(
        SoftwareVersion,
        on_delete=models.CASCADE,
        blank=True, null=True,
        related_name='software_current'
    )
    persistentIdentifier = models.URLField(blank=True, null=True)
    referencePublication = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    conciseDescription = models.TextField(max_length=200, blank=True, null=True)
    softwareFunctionality = models.ManyToManyField(
        Functionality, 
        blank=True, 
        related_name='softwares'
    )
    documentation = models.URLField(blank=True, null=True)
    dataSources = models.ManyToManyField(
        DataInput, 
        blank=True,
        related_name='softwares'
    )
    inputFormats = models.ManyToManyField(
        FileFormat, 
        blank=True, 
        related_name='softwares_to'
    ),
    outputFormats = models.ManyToManyField(
        FileFormat, 
        blank=True, 
        related_name='softwares_from'
    )
    relatedPublications = models.TextField(blank=True, null=True)
    relatedDatasets = models.ManyToManyField(
        RelatedItem,
        blank=True,
        related_name='softwares'
    )
    developmentStatus = models.ForeignKey(
        RepoStatus,
        on_delete=models.CASCADE,
        null=False, blank=False,
        related_name='softwares'
    )
    operatingSystem = models.ManyToManyField(
        OperatingSystem, 
        blank=True, 
        related_name='softwares'
    )
    metadataLicense = models.ForeignKey(
        License,
        on_delete=models.CASCADE, 
        null=True, blank=True, 
        related_name='softwares'
    )
    license = models.ForeignKey(
        License,
        on_delete=models.CASCADE, 
        null=True, blank=True, 
        related_name='softwares_license'
    )
    licenseFileUrl = models.URLField(blank=True, null=True)
    relatedRegion = models.ManyToManyField(
        Region, 
        blank=True, 
        related_name='softwares_region'
    )
    keywords = models.ManyToManyField(
        Keyword, 
        blank=True, 
        related_name='softwares'
    )
    relatedSoftware = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=True
    )
    interoperableSoftware = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=True
    )
    funder = models.ManyToManyField(
        Organization,
        blank=True,
        related_name="softwares_funded"
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
    relatedPhenomena = models.ManyToManyField(
        Phenomena, 
        blank=True,
        related_name='softwares'
    )
    submissionInfo = models.OneToOneField(
        SubmissionInfo,
        on_delete=models.CASCADE,
        blank=True, null=True,
        related_name='software'
    )

    # specified for intellisense, defined in other model
    visible: models.Manager['VisibleSoftware']

    # autogenerated django integer choice string getter
    get_developmentStatus_display: Callable[[], str]

    class Meta:
        ordering = ['softwareName']
        verbose_name_plural = '  Software'

    @classmethod
    def get_top_field(cls) -> models.Field: return cls._meta.get_field("softwareName")

    @classmethod
    def get_subfields(cls):
        subfields = super().get_subfields()
        for i, field in enumerate(subfields):
            if field.name == cls.submissionInfo.name:
                subfields.pop(i)
                break
        return subfields

    def __str__(self): return self.softwareName

    '''if the software is visible on the website'''
    def is_visible(self) -> bool:
        try:
            _ = self.visible
            return True
        except ObjectDoesNotExist: 
            return False

class VisibleSoftware(models.Model):
    '''Stores ids'''
    id = models.OneToOneField(
        Software, 
        on_delete=models.CASCADE, 
        primary_key=True,
        related_name='visible'
    )

    class Meta: 
        ordering = ['id__softwareName']
        verbose_name_plural = 'Visible software'
    def __str__(self):
        return str(self.id)