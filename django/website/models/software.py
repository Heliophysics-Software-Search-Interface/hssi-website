import uuid
from typing import Callable, cast

from django.db import models
from django.core.exceptions import ObjectDoesNotExist

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
    publicationDate = models.DateField(null=True)
    authors = models.ManyToManyField(Person, related_name='softwares')
    publisher = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='softwares'
    )
    relatedInstruments = models.ManyToManyField(
        IvoaEntry,
        blank=True, 
        related_name='softwares'
    )
    relatedObservatories = models.ManyToManyField(
        IvoaEntry,
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
    softwareFunctionality = models.ManyToManyField(
        Functionality, 
        blank=True, 
        related_name='softwares'
    )
    documentation = models.URLField(blank=True, null=True)
    dataInputs = models.ManyToManyField(
        Functionality, 
        blank=True,
        related_name='softwares_data'
    )
    supportedFileFormats = models.ManyToManyField(
        FileFormat, 
        blank=True, 
        related_name='softwares'
    )
    relatedPublications = models.TextField(blank=True, null=True)
    relatedDatasets = models.TextField(blank=True, null=True)
    developmentStatus = models.IntegerField(choices=RepoStatus.choices, default=RepoStatus.WIP)
    operatingSystem = models.ManyToManyField(
        OperatingSystem, 
        blank=True, 
        related_name='softwares'
    )
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
    keywords = models.ManyToManyField(
        Keyword, 
        blank=True, 
        related_name='softwares'
    )
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
    relatedPhenomena = models.ManyToManyField(
        PhenomenaType, 
        blank=True, 
        related_name='softwares'
    )
    submissionInfo = models.ForeignKey(
        SubmissionInfo,
        on_delete=models.CASCADE,
        related_name='software'
    )

    # specified for intellisense, defined in other model
    visible: models.Manager['VisibleSoftware']

    # autogenerated django integer choice string getter
    get_developmentStatus_display: Callable[[], str]

    class Meta:
        ordering = ['softwareName']
        verbose_name_plural = '  Software'
    
    def __str__(self): return self.softwareName

    '''if the software is visible on the website'''
    def is_visible(self) -> bool:
        try:
            _ = self.visible
            return True
        except ObjectDoesNotExist: 
            return False
    
    def get_hssi_data_dict(self) -> dict:
        are_any_authors: bool = self.authors.count() > 0

        # extract author metadata from the authors field
        author_affiliation: str
        author_affiliation_identifier: str
        author_identifier: str
        if are_any_authors:
            first_author: Person = self.authors.first()
            author_identifier = first_author.identifier
            first_author_affiliation: Organization | None = first_author.affiliation
            if first_author_affiliation is not None:
                author_affiliation = first_author_affiliation.name
                author_affiliation_identifier = first_author_affiliation.identifier
            else:
                author_affiliation = None
                author_affiliation_identifier = None
        else:
            author_affiliation = None
            author_identifier = None
            author_affiliation = None
            author_affiliation_identifier = None

        # extract string from publication date if available
        pub_date_str: str | None
        if self.publicationDate: pub_date_str = self.publicationDate.strftime('%Y-%m-%d')
        else: pub_date_str = None

        # create and return the data dictionary
        return {
            'programmingLanguage': self.programmingLanguage.name,
            'publicationDate': pub_date_str,
            'Authors': list(map(
                lambda x: cast(Person, x).to_str_lastname_firstname(),
                self.authors.all()
            )),
            'authorAffiliation': list(map(
                lambda x: cast(Person, x).affiliation.name if x and cast(Person, x).affiliation else None,
                self.authors.all()
            )),
            'authorAffiliationIdentifier': list(map(
                lambda x: cast(Person, x).affiliation.identifier if x and cast(Person, x).affiliation else None,
                self.authors.all()
            )),
            'authorIdentifier': list(map(
                lambda x: cast(Person, x).identifier,
                self.authors.all()
            )),
            'Publisher': self.publisher.name if self.publisher else None,
            'publisherIdentifier': self.publisher.identifier if self.publisher else None,
            'relatedInstruments': list(map(
                lambda x: cast(IvoaEntry, x).name,
                self.relatedInstruments.all()
            )),
            'relatedInstrumentIdentifier': list(map(
                lambda x: cast(IvoaEntry, x).identifier,
                self.relatedInstruments.all()
            )),
            'relatedObservatories': list(map(
                lambda x: cast(IvoaEntry, x).name,
                self.relatedObservatories.all()
            )),
            'softwareName': self.softwareName,
            'versionNumber': self.versionNumber,
            'versionDate': self.versionDate.strftime('%Y-%m-%d'),
            'versionDescription': self.versionDescription,
            'versionPID': self.versionPid,
            'persistentIdentifer': self.persistentIdentifier,
            'referencePublication': self.referencePublication,
            'Description': self.description,
            'conciseDescription': self.conciseDescription,
            'softwareFunctionality': list(map(
                lambda x: cast(Functionality, x).name,
                self.softwareFunctionality.all()
            )),
            'Documentation': self.documentation,
            'dataInputs': list(map(
                lambda x: cast(Functionality, x).name,
                self.dataInputs.all()
            )),
            'supportedFileFormats': list(map(
                lambda x: cast(FileFormat, x).extension,
                self.supportedFileFormats.all()
            )),
            'relatedPublications': self.relatedPublications,
            'relatedDatasets': self.relatedDatasets,
            'developmentStatus': RepoStatus(self.developmentStatus).name,
            'operatingSystem': self.operatingSystem.name,
            'processorArchitecture': None,
            'processorTopologyType': None,
            'metadataLicense': self.metadataLicense.name if self.metadataLicense else None,
            'metadatalicenseURI': self.metadataLicense.url if self.metadataLicense else None,
            'metadatalicenseIdentifier': self.metadataLicense.identifier if self.metadataLicense else None,
            'metadatalicenseIdentifierScheme': self.metadataLicense.scheme if self.metadataLicense else None,
            'metadataschemeURI': self.metadataLicense.scheme_url if self.metadataLicense else None,
            'License': self.license.name if self.license else None,
            'licenseURI': self.license.url if self.license else None,
            'licenseIdentifier': self.license.identifier if self.license else None,
            'licenseIdentifierScheme': self.license.scheme if self.license else None,
            'schemeURI': self.license.scheme_url if self.license else None,
            'relatedRegion': self.relatedRegion,
            'Keywords': list(map(
                lambda x: cast(Keyword, x).name,
                self.keywords.all()
            )),
            'relatedSoftware': self.relatedSoftware,
            'interoperableSoftware': self.interopableSoftware,
            'funder': self.funder.name if self.funder else None,
            'funderIdentifier': self.funder.identifier if self.funder else None,
            'awardTitle': self.award.name if self.award else None,
            'awardNumber': self.award.identifier if self.award else None,
            'codeRepositoryURL': self.codeRepositoryUrl,
            'Logo': self.logo.url if self.logo else None,
            'relatedPhenomena': list(map(
                lambda x: cast(PhenomenaType, x).name,
                self.relatedPhenomena.all()
            )),
        }

class VisibleSoftware(models.Model):
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