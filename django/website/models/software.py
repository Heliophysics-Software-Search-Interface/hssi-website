"""
Contains primary software entry data model and directly related models.

These are versions, submission/curation info, the public-visibility flag, and
the edit-link queue. Touch this when adding a software metadata field or
changing how submissions are tracked or published.
"""

from __future__ import annotations
import datetime, uuid
from typing import Callable

from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.core.exceptions import ObjectDoesNotExist
from sortedm2m.fields import SortedManyToManyField

from ..util import *
from .people import Person, Submitter, Curator
from .related import RelatedItem
from .organizations import Award, Organization
from .base import LEN_NAME, HssiModel, HssiSet
from .license import License
from .vocab import (
	RepoStatus, OperatingSystem, Keyword, Phenomena, 
	InstrumentObservatory, ProgrammingLanguage, FileFormat, 
	Region, DataInput, FunctionCategory, CpuArchitecture
)

# TODO (temporary hack): The SciX URLs below are hardcoded because adding
# a real `scix_url` field to the Software model (migration, admin form,
# import/export plumbing, submission UI) isn't justified for a 5-entry
# proof-of-concept. When SciX coverage expands, replace this dict and the
# `scix_url` property/serialization below with a real URLField on Software.
_SCIX_URLS: dict[str, str] = {
	"82f57fc4-357f-49d3-af4b-e8bfb0a35210": "https://scixplorer.org/abs/2024ascl.soft05005G/abstract",  # PySPEDAS
	"13b71402-f2cb-4aa3-9b17-639652e87ca8": "https://scixplorer.org/abs/2025zndo..17857260M/abstract",  # sunpy
	"7bd65217-fdbe-4945-a657-496a494fff48": "https://scixplorer.org/abs/2024zndo..14057789M/abstract",  # SpacePy
	"4507d98e-44d1-40ea-8733-8047738b9a7a": "https://scixplorer.org/abs/2024zndo..12788848C/abstract",  # PlasmaPy
	"f6e3429d-e80e-4cf6-889e-44af1e93f87d": "https://scixplorer.org/abs/2021zndo...5553156W/abstract",  # hapi server/client python
}

class SubmissionStatusCode(models.IntegerChoices):
	"""
	Integer choices for a submission's internal curation state, from
	`PROPOSED_RESOURCE` (1) through `SPAM` (10).
	"""
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

class SoftwareVersion(HssiModel):
	"""A snapshot of the software metadata whenever it's updated to a new version"""
	access = AccessLevel.PUBLIC
	number = models.CharField(max_length=LEN_NAME)
	"""Version number string."""
	release_date = models.DateField(blank=True, null=True)
	"""Date the version was released."""
	description = models.TextField(blank=True, null=True)
	"""Release notes or description of the version."""
	version_pid = models.URLField(blank=True, null=True)
	"""Persistent identifier URL for this version."""
	
	# specified for intellisense, defined in Software model
	software: models.Manager['Software']
	"""Reverse relation to the `Software` entries that list this version."""

	@classmethod
	def get_top_field(cls) -> models.Field:
		"""Returns the `number` field as the model's display field."""
		return cls._meta.get_field("number")

	def __str__(self):
		if self.software.first():
			return f"{self.software.first()} - {self.number}"
		return self.number

	class Meta: ordering = ['number']

class Software(HssiModel):
	"""
	A software entry in the catalog, holding all of its submitted metadata.
	"""
	access = AccessLevel.CURATOR
	programming_language: Manager[ProgrammingLanguage] = models.ManyToManyField(
		ProgrammingLanguage,
		blank=True, 
		related_name='softwares'
	)
	"""`ProgrammingLanguage`s the software is written in."""
	publication_date = models.DateField(blank=True, null=True)
	"""Date the software was published."""
	publisher = models.ForeignKey(
		Organization,
		on_delete=models.SET_NULL, 
		null=True, 
		blank=True, 
		related_name='softwares_published'
	)
	"""Publishing `Organization`."""
	authors: Manager[Person] = SortedManyToManyField(Person, related_name='softwares')
	"""Ordered list of author `Person`s."""
	related_instruments: Manager[InstrumentObservatory] = models.ManyToManyField(
		InstrumentObservatory,
		blank=True, 
		related_name='softwares'
	)
	"""Related instruments (`InstrumentObservatory`)."""
	related_observatories: Manager[InstrumentObservatory] = models.ManyToManyField(
		InstrumentObservatory,
		blank=True, 
		related_name='observatories'
	)
	"""Related observatories (`InstrumentObservatory`)."""
	software_name = models.CharField(max_length=LEN_NAME)
	"""Name of the software."""
	version: Manager[SoftwareVersion] = models.ManyToManyField(
		SoftwareVersion,
		blank=True,
		related_name='software'
	)
	"""`SoftwareVersion`s of this software."""
	persistent_identifier = models.URLField(blank=True, null=True)
	"""Persistent identifier URL (e.g. DOI)."""
	reference_publication = models.ForeignKey(
		RelatedItem,
		on_delete=models.SET_NULL,
		blank=True, null=True,
		related_name="softwares_published"
	)
	"""The `RelatedItem` to cite as the software's reference publication."""
	description = models.TextField(blank=True, null=True)
	"""Full description."""
	concise_description = models.TextField(max_length=200, blank=True, null=True)
	"""Short description, max 200 characters."""
	software_functionality: Manager[FunctionCategory] = SortedManyToManyField(
		FunctionCategory, 
		blank=True, 
		related_name='softwares'
	)
	"""Ordered `FunctionCategory` tags."""
	documentation = models.URLField(blank=True, null=True)
	"""Documentation URL."""
	data_sources: Manager[DataInput] = models.ManyToManyField(
		DataInput, 
		blank=True,
		related_name='softwares'
	)
	"""`DataInput` vocabulary terms."""
	input_formats: Manager[FileFormat] = models.ManyToManyField(
		FileFormat, 
		blank=True, 
		related_name='softwares_in'
	)
	"""Supported input `FileFormat`s."""
	output_formats: Manager[FileFormat] = models.ManyToManyField(
		FileFormat, 
		blank=True, 
		related_name='softwares_out'
	)
	"""Supported output `FileFormat`s."""
	cpu_architecture: Manager[CpuArchitecture] = models.ManyToManyField(
		CpuArchitecture,
		blank=True,
		related_name='softwares'
	)
	"""Supported `CpuArchitecture`s."""
	related_publications: Manager[RelatedItem] = models.ManyToManyField(
		RelatedItem,
		blank=True,
		related_name='softwares_referenced'
	)
	"""Related publications (`RelatedItem`)."""
	related_datasets: Manager[RelatedItem] = models.ManyToManyField(
		RelatedItem,
		blank=True,
		related_name='softwares_data'
	)
	"""Related datasets (`RelatedItem`)."""
	development_status = models.ForeignKey(
		RepoStatus,
		on_delete=models.SET_NULL,
		null=True, blank=True,
		related_name='softwares'
	)
	"""`RepoStatus` term describing development status."""
	operating_system: Manager[OperatingSystem] = models.ManyToManyField(
		OperatingSystem, 
		blank=True, 
		related_name='softwares'
	)
	"""Supported `OperatingSystem`s."""
	license = models.ForeignKey(
		License,
		on_delete=models.SET_NULL, 
		null=True, blank=True, 
		related_name='softwares_license'
	)
	"""The software's `License`."""
	related_region: Manager[Region] = SortedManyToManyField(
		Region, 
		blank=True, 
		related_name='softwares_region'
	)
	"""Ordered `Region` terms."""
	keywords: Manager[Keyword] = models.ManyToManyField(
		Keyword, 
		blank=True, 
		related_name='softwares'
	)
	"""`Keyword` terms."""
	related_software: Manager[RelatedItem] = models.ManyToManyField(
		RelatedItem,
		blank=True,
		related_name='softwares_related'
	)
	"""Related software (`RelatedItem`)."""
	interoperable_software: Manager[RelatedItem] = models.ManyToManyField(
		RelatedItem,
		blank=True,
		related_name='softwares_interoperable'
	)
	"""Software this interoperates with (`RelatedItem`)."""
	funder: Manager[Organization] = models.ManyToManyField(
		Organization,
		blank=True,
		related_name="softwares_funded"
	)
	"""Funding `Organization`s."""
	award: Manager[Award] = models.ManyToManyField(
		Award,
		blank=True, 
		related_name='softwares'
	)
	"""Funding `Award`s."""
	code_repository_url = models.URLField(blank=True, null=True)
	"""Source repository URL."""
	logo = models.URLField(blank=True, null=True)
	"""Logo image URL."""
	date_modified = models.DateTimeField(null=True, blank=True, editable=False)
	"""
	Last change to this record's metadata through the supported write paths: the
	admin change form (only when the form reports changed fields), the
	submission serializer's create/update (POST /api/submission/ and PATCH), and
	the submission parser (public form, legacy /api/submit, edit link).
	Deliberately not stamped: edits to related rows alone (Person, Organization,
	Award, RelatedItem, License, SoftwareVersion, vocab), SubmissionInfo edits,
	publishing, slug changes, the collapse/fix-uuid/fetch-vocab admin actions,
	CSV import/restore, and bulk or raw SQL writes. Null means "not stamped
	yet"; the JSON-LD falls back to the newest submission date. See issue #103.
	"""
	related_phenomena: Manager[Phenomena] = SortedManyToManyField(
		Phenomena, 
		blank=True,
		related_name='softwares'
	)
	"""Ordered `Phenomena` terms."""

	# specified for intellisense, defined in other model
	submission_info: Manager[SubmissionInfo]
	"""Reverse relation to this software's `SubmissionInfo` entries."""
	visible: models.Manager[VerifiedSoftware]
	"""
	Reverse relation to its `VerifiedSoftware` row, present only if published.
	"""

	# autogenerated django integer choice string getter
	get_development_status_display: Callable[[], str]
	"""Display label of `development_status` (generated by Django)."""

	class Meta:
		ordering = ['software_name']
		verbose_name_plural = '  Software'

	@classmethod
	def get_top_field(cls) -> models.Field:
		"""Returns the `software_name` field as the model's display field."""
		return cls._meta.get_field("software_name")

	@classmethod
	def get_subfields(cls):
		"""The model's subfields, excluding `submission_info`."""
		subfields = super().get_subfields()
		for i, field in enumerate(subfields):
			if field.name == cls.submission_info.name:
				subfields.pop(i)
				break
		return subfields

	def get_ordered_software_functionality(self) -> list[FunctionCategory]:
		"""Return functionality tags with parent/child groups kept together."""
		categories = list(
			self.software_functionality.prefetch_related("parent_nodes").all()
		)
		parent_map = {
			category.id: list(category.parent_nodes.all())
			for category in categories
		}
		groups: dict[uuid.UUID, list[FunctionCategory]] = {}
		for category in categories:
			parents = parent_map[category.id]
			group_id = parents[0].id if parents else category.id
			groups.setdefault(group_id, []).append(category)

		ordered: list[FunctionCategory] = []
		for group in groups.values():
			ordered.extend(
				sorted(group, key=lambda category: bool(parent_map[category.id]))
			)
		return ordered

	def latest_version(self) -> SoftwareVersion | None:
		"""The version with the latest release date, or the highest number if none has a date."""
		versions = list(self.version.all())
		if not versions:
			return None
		with_dates = [v for v in versions if v.release_date]
		if with_dates:
			return max(with_dates, key=lambda v: v.release_date)
		return sorted(versions, key=lambda v: v.number)[-1]

	@property
	def scix_url(self) -> str | None:
		"""
		SciX abstract URL for this software, from a small hardcoded list; `None`
		for most entries.
		"""
		return _SCIX_URLS.get(str(self.id))

	def get_serialized_data(self, *args, **kwargs):
		"""Serialized data from `HssiModel`, plus `scix_url`."""
		data = super().get_serialized_data(*args, **kwargs)
		data["scix_url"] = self.scix_url
		return data

	def __str__(self): return self.software_name

	def get_absolute_url(self):
		"""
		URL of the software's detail page, by slug if published, otherwise by
		UUID.
		"""
		from django.urls import reverse
		verified = VerifiedSoftware.objects.filter(pk=self.pk).only("slug").first()
		if verified and verified.slug:
			return reverse('website:software_detail', kwargs={'slug': verified.slug})
		return reverse('website:software_detail', kwargs={'pk': str(self.pk)})

	def is_visible(self) -> bool:
		"""If the software is visible on the website."""
		try:
			_ = self.visible
			return True
		except ObjectDoesNotExist: 
			return False

class SubmissionInfo(HssiModel):
	"""Metadata about the a piece of software submitted to HSSI"""
	access = AccessLevel.CURATOR
	software = models.ForeignKey(
		Software,
		on_delete=models.CASCADE,
		blank=True, null=True,
		related_name='submission_info'
	)
	"""The `Software` this submission is for."""
	date_modified = models.DateTimeField(auto_now=True, blank=True, null=True)
	"""Last time this submission info was saved."""
	modification_description = models.TextField(blank=True, null=True)
	"""Note describing the latest modification."""
	metadata_version_number = models.CharField(max_length=50, blank=True, null=True)
	"""Version of the metadata schema used."""
	submitter = models.ManyToManyField(
		Submitter,
		default=Submitter.get_default_submitter,
		blank=True,
		related_name='submission_infos'
	)
	"""
	`Submitter`s of the entry; defaults to the placeholder "UNKNOWN" submitter.
	"""
	curator = models.ForeignKey(
		Curator,
		on_delete=models.SET_NULL, 
		null=True, blank=True, 
		related_name='submission_infos'
	)
	"""Assigned `Curator`."""
	submission_date = models.DateTimeField(blank=True, null=True)
	"""When the entry was submitted."""
	internal_status_code = models.IntegerField(
		choices=SubmissionStatusCode.choices, 
		default=SubmissionStatusCode.PROPOSED_RESOURCE
	)
	"""Curation state, a `SubmissionStatusCode`."""
	internal_status_note = models.TextField(blank=True, null=True)
	"""Curator notes on the status."""
	lead_curator = models.ForeignKey(
		Curator,
		on_delete=models.SET_NULL, 
		null=True, blank=True, 
		related_name='submission_infos_led'
	)
	"""Lead `Curator`."""
	last_contact_date = models.DateField(blank=True, null=True)
	"""Date the submitter was last contacted."""
	contact_count = models.IntegerField(default=0)
	"""Number of times the submitter has been contacted."""
	curator_lock = models.BooleanField(default=False)
	"""Flag marking the entry as locked by a curator."""
	out_of_sync = models.BooleanField(default=False)
	"""Flag marking the entry as out of sync with its source metadata."""

	# autogenerated django integer choice string getter
	get_internal_status_code_display: Callable[[], str]
	"""Display label of `internal_status_code` (generated by Django)."""

	@classmethod
	def get_top_field(cls) -> models.Field:
		"""Returns the `submitter` field as the model's display field."""
		return cls._meta.get_field("submitter")

	class Meta: 
		ordering = ['date_modified']
		verbose_name_plural = "  Submission Info"
	def __str__(self): 
		text = "Submission"
		if self.submitter: text += f" by {str(self.submitter)}"
		text += f" on {str(self.submission_date)}"
		return text

class VerifiedSoftware(HssiSet):
	"""Stores ids to flag softwares with the given ids as visible"""
	access = AccessLevel.PUBLIC
	target_model = Software
	slug = models.CharField(max_length=LEN_NAME, unique=True, null=True)
	"""Unique URL slug for the software's detail page."""

	@classmethod
	def create_verified(cls, software: Software) -> 'VerifiedSoftware':
		"""
		Publishes a software with a new unique slug; returns `None` if it's
		already published.
		"""
		if cls.objects.filter(pk=software.pk).first():
			return None
		obj = VerifiedSoftware.objects.create(
			id=uuid.UUID(str(software.id)), 
			slug=cls.get_unique_slug(software.software_name)
		)
		print(f"made {software.software_name}:{software.id} visible to public at slug '{obj.slug}'")
		return obj
	
	@classmethod
	def get_unique_slug(cls, name: str) -> str:
		"""
		Builds a slug from a name, appending `-2`, `-3`, … until it's unique.
		"""
		slug_orig = slugify(name.lower().replace("/","-").replace(".","-"))
		slug = slug_orig[:LEN_NAME]

		# append '-n' on the end until it is a unique slug
		iter = 1
		while VerifiedSoftware.objects.filter(slug=slug).first():
			iter += 1
			num_str = f"-{iter}"
			slug = slug_orig[:LEN_NAME-len(num_str)] + num_str
		
		return slug

	class Meta: verbose_name_plural = 'Verified software'

class SoftwareEditQueue(HssiModel):
	"""
	The idea here is that submitters can request to make edits to their 
	submissions by accessing the page for their software package, then press a 
	button to request to edit their submission. When the option is selected,
	a new entry will be made into this model, pointing to the target software
	to be edited, then an email will be sent to the submitter email linking to
	the edit page made from the entry in this model. The edit page will expire 
	some time after it is created. This allows for secure editing of submissions
	by the submitter with a randomly generated url based on the UUID of the 
	object in this model's pk without managing profiles for submitters.
	"""

	default_expire_delta = datetime.timedelta(hours=5)
	"""Default link lifetime, 5 hours."""

	access = AccessLevel.PUBLIC
	created = models.DateTimeField(null=True, blank=True)
	"""When the link was created."""
	expiration = models.DateTimeField(null=True, blank=True)
	"""When the link expires."""
	target_software = models.ForeignKey(
		Software, 
		on_delete=models.CASCADE,
		null=True, blank=True,
		related_name="submission_edit_queue"
	)
	"""The `Software` the link edits."""

	def is_expired(self) -> bool:
		"""
		returns true if the queue entry was created longer ago than the 
		threshold specifies, the entry should be deleted if this returns true
		"""
		if not self.expiration: return True
		return timezone.now() > self.expiration
	
	@classmethod
	def get_latest_expiry(cls, target: Software) -> 'SoftwareEditQueue':
		"""
		grab the edit queue item that corresponds to the specified target 
		which has the latest expiry date/time
		"""
		items = cls.objects.filter(target_software=target.pk)
		latest = items.first()
		if not latest: return None
		for item in items:
			if latest.expiration < item.expiration: latest = item
		return latest

	@classmethod
	def create(cls, target: Software, expiration: datetime.datetime = None) -> 'SoftwareEditQueue':
		"""
		Creates and saves a link for a software, expiring after
		`default_expire_delta` unless given.
		"""
		queue_item = cls()
		queue_item.created = timezone.now()
		queue_item.target_software = target
		if not expiration: expiration = queue_item.created + cls.default_expire_delta
		queue_item.expiration = expiration
		queue_item.save()
		return queue_item
