from django.db import models

from typing import Callable, TYPE_CHECKING
if TYPE_CHECKING:
	from .software import Software

from ..util import *
from .people import HssiModel, Curator, Submitter

class SubmissionStatusCode(models.IntegerChoices):
	PROPOSED_RESOURCE = 1, "Proposed Resource"
	READY_FOR_CONTACT = 2, "Ready for Contact"
	CONTACTED = 3, "Contacted"
	RESOURCE_DEV_PAUSED = 4, "Resource Dev Paused"
	RECEIVED = 5, "Received"
	IN_REVIEW_INTERNAL = 6, "In Review (Our End)"
	IN_REVIEW_EXTERNAL = 7, "In Review (Their End)"
	RESOURCE_CREATED = 8, "Resource Created (Published)"
	REJECTED = 9, "Rejected/Abandoned"
	SPAM = 10, "Spam"

class SubmissionInfo(HssiModel):
	'''Metadata about the a piece of software submitted to HSSI'''
	access = AccessLevel.CURATOR
	dateModified = models.DateField(auto_now=True, blank=True, null=True)
	modificationDescription = models.TextField(blank=True, null=True)
	metadataVersionNumber = models.CharField(max_length=50, blank=True, null=True)
	submitter = models.ForeignKey(
		Submitter,
		on_delete=models.CASCADE, 
		blank=True,
		related_name='submission_infos'
	)
	curator = models.ForeignKey(
		Curator,
		on_delete=models.CASCADE, 
		null=True, 
		blank=True, 
		related_name='submission_infos'
	)
	submissionDate = models.DateField(blank=True, null=True)
	internalStatusCode = models.IntegerField(
		choices=SubmissionStatusCode.choices, 
		default=SubmissionStatusCode.PROPOSED_RESOURCE
	)
	internalStatusNote = models.TextField(blank=True, null=True)
	leadCurator = models.ForeignKey(
		Curator,
		on_delete=models.CASCADE, 
		null=True, 
		blank=True, 
		related_name='submission_infos_led'
	)
	lastContactDate = models.DateField(blank=True, null=True)
	contactCount = models.IntegerField(default=0)
	curatorLock = models.BooleanField(default=False)
	outOfSync = models.BooleanField(default=False)

	# specified for intellisense, defined in other model
	software: models.Manager['Software']

	# autogenerated django integer choice string getter
	get_internalStatusCode_display: Callable[[], str]

	@classmethod
	def get_top_field(cls) -> models.Field: return cls._meta.get_field("submitter")

	class Meta: 
		ordering = ['dateModified']
		verbose_name_plural = "  Submission Info"
	def __str__(self): 
		text = "Submission"
		if self.submitter: text += f" by {str(self.submitter)}"
		text += f" on {str(self.submissionDate)}"
		return text
