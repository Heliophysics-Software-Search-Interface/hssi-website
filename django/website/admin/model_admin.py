import uuid, json

from import_export import resources
from import_export.admin import ImportExportModelAdmin
from django.utils import timezone
from django.contrib.admin import action, register
from django.http import HttpRequest
from django.db.models import QuerySet, ManyToManyField

from ..views import email_edit_link as v_email_edit_link
from ..models.people import Person, Curator
from ..models.software import (
    Software, VisibleSoftware, SoftwareVersion, SoftwareEditQueue,
)
from ..models.submission_info import SubmissionInfo
from ..models.auxillary_info import RelatedItem, Award
from ..models.roots import (
	HssiModel, ControlledList, FunctionCategory, OperatingSystem, Phenomena, 
	Keyword, Image, Organization, License, InstrumentObservatory, RepoStatus, 
	DataInput, ProgrammingLanguage, FileFormat, Region
)

from ..util import *

# Abstract definitions for model admins ----------------------------------------

class HSSIModelAdmin(ImportExportModelAdmin):

	@action(description="Fix Improper Toplevel UUID")
	def fix_uuid_chains(self, request: HttpRequest, queryset: QuerySet):
		"""
		Due to an error that should now be fixed, software submission entries
		would sometimes subit new model entries for certain fields where the 
		model object's name would be a uuid, when instead it should have been
		treated as a reference to another object instead of creating a new 
		object with that uuid as a name. 
		This is an action that appears in the admin control panel as a 
		retroactive solution that aims to resolve these faulty foregn key/m2m
		references.
		"""
		hssimodel = queryset.model
		if not issubclass(hssimodel, HssiModel): return
		topfield = hssimodel.get_top_field()
	
		for obj in queryset:

			iter_obj = obj
			val: str = ""
			uid: uuid.UUID = None
			iters: int = 0

			# it is possible for a false key to refer to another false key,
			# which then needs to be resolved further. Multiple iterations 
			# should solve this by continuing to resolve false keys until a
			# non-key value is found
			while True:
				val = getattr(iter_obj, topfield.name)
				try: uid = uuid.UUID(val)
				except Exception: break
				iter_obj = hssimodel.objects.get(pk=uid)
				iters += 1
				if iters >= 100: break

			if iters <= 0: 
				print(f"'{str(val)}' does not appear to be a uuid")
				continue

			print(f"false key depth for {str(obj)}: {iters}")
			refobj = hssimodel.objects.filter(pk=uid).first()
			if not refobj:
				print(f"could not find {uid} in {hssimodel._meta.model_name}")
				continue
			
			# fix all references to this false key that should instead be 
			# pointing to the object that this key resolves to
			refs = find_database_references(obj)
			print(f"updating {len(refs)} references to {str(uid)}..")
			for ref in refs:
				target, field = ref

				# many to many fields need to be handled separately since they
				# hold multiple foreign key references instead of just one
				if isinstance(field, ManyToManyField): 
					manager = getattr(target, field.name)
					manager.remove(obj)
					manager.add(refobj)
				else: setattr(target, field.name, refobj)
				target.save()
				print(f"updated '{target}:{field}' field")
	

	@action(description="Collapse to Single")
	def collapse_model_entries(
		self, 
		request: HttpRequest, 
		queryset: QuerySet[ControlledList]
	):
		"""
		Useful for if there are multiple entries that should be treated as the 
		same, use this action to collapse all objects to one object, and update
		all references to those objects to point to the new combined object.
		The fields of the combined object will be equal to the first selected 
		object, and appended to if there are any empty fields on that object.
		"""
		HssiModel.collapse_objects(queryset)

	# actions need to be specified
	actions = [fix_uuid_chains, collapse_model_entries]

	# columns to display in the model admin page
	list_display = ('str_display', 'id')

	def str_display(self, obj: Model): return str(obj)

# Admin definitions for roots module -------------------------------------------

class OperatingSystemResource(resources.ModelResource):
	class Meta: model = OperatingSystem
class OperatingSystemAdmin(HSSIModelAdmin): resource_class = OperatingSystemResource

class PhenomenaTypeResource(resources.ModelResource):
	class Meta: model = Phenomena
class PhenomenaTypeAdmin(HSSIModelAdmin): resource_class = PhenomenaTypeResource

class KeywordResource(resources.ModelResource):
	class Meta: model = Keyword
class KeywordAdmin(HSSIModelAdmin): 
	resource_class = KeywordResource

	@action(description="Collapse to Single")
	def collapse_keyword_entries(self, request: HttpRequest, queryset: QuerySet[Keyword]):
		colkeyword = Keyword.collapse_objects(queryset)
		colkeyword.name = SPACE_REPLACE.sub(' ', colkeyword.name).lower()
		colkeyword.save()
	
	@action(description="Format Names")
	def format_names(self, req: HttpRequest, query: QuerySet[Keyword]):
		for obj in query:
			obj.name = SPACE_REPLACE.sub(' ', obj.name).lower()
			obj.save()

	actions = [
		HSSIModelAdmin.fix_uuid_chains,
		collapse_keyword_entries,
		format_names,
	]

class ImageResource(resources.ModelResource):
	class Meta: model = Image
class ImageAdmin(HSSIModelAdmin): resource_class = ImageResource

class RegionResource(resources.ModelResource):
	class Meta: model = Region
class RegionAdmin(HSSIModelAdmin): resource_class = RegionResource

class DataInputResource(resources.ModelResource):
	class Meta: model = DataInput
class DataInputAdmin(HSSIModelAdmin): resource_class = DataInputResource

class RepoStatusResource(resources.ModelResource):
	class Meta: model = RepoStatus
class RepoStatusAdmin(HSSIModelAdmin): resource_class = RepoStatusResource

class FunctionCategoryResource(resources.ModelResource):
	class Meta: model = FunctionCategory
class FunctionCategoryAdmin(HSSIModelAdmin): resource_class = FunctionCategoryResource

class InstrumentObservatoryResource(resources.ModelResource):
	class Meta: model = InstrumentObservatory
class InstrumentObservatoryAdmin(HSSIModelAdmin): resource_class = InstrumentObservatoryResource

class LicenseResource(resources.ModelResource):
	class Meta: model = License
class LicenseAdmin(HSSIModelAdmin): 
	resource_class = LicenseResource

	def str_display(self, obj: Model): 
		disp = super().str_display(obj)
		if isinstance(obj, License):
			if obj.name == "Other" and obj.url: disp += " - " + obj.url
		return disp

class OrganizationResource(resources.ModelResource):
	class Meta: model = Organization
class OrganizationAdmin(HSSIModelAdmin): resource_class = OrganizationResource

class FileFormatResource(resources.ModelResource):
	class Meta: model = FileFormat
class FileFormatAdmin(HSSIModelAdmin): resource_class = FileFormatResource

class ProgrammingLanguageResource(resources.ModelResource):
	class Meta: model = ProgrammingLanguage
class ProgrammingLanguageAdmin(HSSIModelAdmin): resource_class = ProgrammingLanguageResource

# Admin definitions for people module ------------------------------------------

class PersonResource(resources.ModelResource): 
	class Meta: model = Person
class PersonAdmin(HSSIModelAdmin): resource_class = PersonResource

class CuratorResource(resources.ModelResource):
	class Meta: model = Curator
class CuratorAdmin(HSSIModelAdmin): resource_class = CuratorResource

class SubmitterResource(resources.ModelResource):
	class Meta: model = Person
class SubmitterAdmin(HSSIModelAdmin): resource_class = SubmitterResource

# Admin definitions for Auxillary Info -----------------------------------------

class AwardResource(resources.ModelResource):
	class Meta: model = Award
class AwardAdmin(HSSIModelAdmin): resource_class = AwardResource

class DatasetResource(resources.ModelResource):
	class Meta: model = RelatedItem
class DatasetAdmin(HSSIModelAdmin): resource_class = DatasetResource

class SoftwareVersionResource(resources.ModelResource):
	class Meta: model = SoftwareVersion
class SoftwareVersionAdmin(HSSIModelAdmin): resource_class = SoftwareVersionResource

# Admin definitions for software module ----------------------------------------

class SoftwareResource(resources.ModelResource):
	class Meta: model = Software
class SoftwareAdmin(HSSIModelAdmin):
	resource_class = SoftwareResource

	@action(description="Publish to Visible Software")
	def mark_visible(self, 
		request: HttpRequest, 
		queryset: QuerySet[Software]
	):
		for soft in queryset:
			exists = not not VisibleSoftware.objects.filter(pk=soft.pk).first()
			if exists: continue
			VisibleSoftware.objects.create(id=uuid.UUID(str(soft.id)))
			print(f"made {soft.softwareName}:{soft.id} visible to public")

	@action(description="Add to Edit Queue")
	def add_edit_queue(self, request: HttpRequest, queryset: QuerySet[Software]):
		for soft in queryset: SoftwareEditQueue.create(soft)

	actions = [
		mark_visible,
		add_edit_queue,
		HSSIModelAdmin.fix_uuid_chains, 
		HSSIModelAdmin.collapse_model_entries,
	]

class VisibleSoftwareResource(resources.ModelResource):
	class Meta: model = VisibleSoftware
class VisibleSoftwareAdmin(ImportExportModelAdmin): resource_class = VisibleSoftwareResource

class SoftwareEditQueueResource(resources.ModelResource):
	class Meta: Model = SoftwareEditQueue
class SoftwareEditQueueAdmin(ImportExportModelAdmin):
	resource_class = SoftwareEditQueueResource

	list_display = ('target_name', 'created', 'id')

	@action(description="Prune expired items")
	def remove_selected(self, request: HttpRequest, query: QuerySet[SoftwareEditQueue]):
		to_remove: list[SoftwareEditQueue] = []

		for item in query:
			elapsed = timezone.now() - item.created
			if elapsed > item.default_expire_delta:
				print(f"removing '{self.target_name(item)}' from editable queue")
				to_remove.append(item)
		
		for item in to_remove: item.delete()

	def target_name(self, obj: 'SoftwareEditQueue') -> str:
		if obj.target_software: return obj.target_software.softwareName
		return "None"
	
	actions = [
		remove_selected
	]


# Admin definitions for submission_info module ---------------------------------

class SubmissionInfoResource(resources.ModelResource):
	class Meta: model = SubmissionInfo
class SubmissionInfoAdmin(HSSIModelAdmin): 
	resource_class = SubmissionInfoResource

	@action(description="Email edit submission link")
	def email_edit_link(self, request: HttpRequest, query: QuerySet[SubmissionInfo]):
		for info in query: v_email_edit_link(info)

	actions = [
		email_edit_link,
		HSSIModelAdmin.fix_uuid_chains,
		HSSIModelAdmin.collapse_model_entries,
	]

	def submission_name(self, obj: SubmissionInfo):
		return obj.software.softwareName

	def submitter_name(self, obj: SubmissionInfo):
		if obj.submitter: return obj.submitter.fullName
		return "None"
	
	list_display = ('submission_name', 'submitter_name', 'submissionDate', 'id')