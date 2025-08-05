import uuid

from import_export import resources
from import_export.admin import ImportExportModelAdmin
from django.contrib.admin import action, register
from django.http import HttpRequest
from django.db.models import QuerySet, ManyToManyField

from ..models.people import Person, Curator
from ..models.software import Software, VisibleSoftware, SoftwareVersion
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
	
	# actions need to be specified
	actions = [fix_uuid_chains]

class ControlledListAdmin(HSSIModelAdmin):

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
		ControlledList.collapse_objects(queryset)

	actions = [HSSIModelAdmin.fix_uuid_chains, collapse_model_entries]

# Admin definitions for roots module -------------------------------------------

class OperatingSystemResource(resources.ModelResource):
	class Meta: model = OperatingSystem
class OperatingSystemAdmin(ControlledListAdmin): resource_class = OperatingSystemResource

class PhenomenaTypeResource(resources.ModelResource):
	class Meta: model = Phenomena
class PhenomenaTypeAdmin(ControlledListAdmin): resource_class = PhenomenaTypeResource

class KeywordResource(resources.ModelResource):
	class Meta: model = Keyword
class KeywordAdmin(ControlledListAdmin): 
	resource_class = KeywordResource

	@action(description="Collapse to Single")
	def collapse_keyword_entries(self, request: HttpRequest, queryset: QuerySet[Keyword]):
		colkeyword = Keyword.collapse_objects(queryset)
		colkeyword.name = SPACE_REPLACE.sub(' ', colkeyword.name).lower()
		colkeyword.save()
	
	@action(description="Format Names")
	def format_name(self, req: HttpRequest, query: QuerySet[Keyword]):
		for obj in query:
			obj.name = SPACE_REPLACE.sub(' ', obj.name).lower()
			obj.save()

	actions = [
		HSSIModelAdmin.fix_uuid_chains,
		collapse_keyword_entries,
		format_name,
	]

class ImageResource(resources.ModelResource):
	class Meta: model = Image
class ImageAdmin(HSSIModelAdmin): resource_class = ImageResource

class RegionResource(resources.ModelResource):
	class Meta: model = Region
class RegionAdmin(ControlledListAdmin): resource_class = RegionResource

class DataInputResource(resources.ModelResource):
	class Meta: model = DataInput
class DataInputAdmin(ControlledListAdmin): resource_class = DataInputResource

class RepoStatusResource(resources.ModelResource):
	class Meta: model = RepoStatus
class RepoStatusAdmin(ControlledListAdmin): resource_class = RepoStatusResource

class FunctionCategoryResource(resources.ModelResource):
	class Meta: model = FunctionCategory
class FunctionCategoryAdmin(ControlledListAdmin): resource_class = FunctionCategoryResource

class InstrumentObservatoryResource(resources.ModelResource):
	class Meta: model = InstrumentObservatory
class InstrumentObservatoryAdmin(ControlledListAdmin): resource_class = InstrumentObservatoryResource

class LicenseResource(resources.ModelResource):
	class Meta: model = License
class LicenseAdmin(HSSIModelAdmin): resource_class = LicenseResource

class OrganizationResource(resources.ModelResource):
	class Meta: model = Organization
class OrganizationAdmin(HSSIModelAdmin): resource_class = OrganizationResource

class FileFormatResource(resources.ModelResource):
	class Meta: model = FileFormat
class FileFormatAdmin(ControlledListAdmin): resource_class = FileFormatResource

class ProgrammingLanguageResource(resources.ModelResource):
	class Meta: model = ProgrammingLanguage
class ProgrammingLanguageAdmin(ControlledListAdmin): resource_class = ProgrammingLanguageResource

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
class DatasetAdmin(ControlledListAdmin): resource_class = DatasetResource

class SoftwareVersionResource(resources.ModelResource):
	class Meta: model = SoftwareVersion
class SoftwareVersionAdmin(HSSIModelAdmin): resource_class = SoftwareVersionResource

# Admin definitions for software module ----------------------------------------

class SoftwareResource(resources.ModelResource):
	class Meta: model = Software
class SoftwareAdmin(HSSIModelAdmin): resource_class = SoftwareResource

class VisibleSoftwareResource(resources.ModelResource):
	class Meta: model = VisibleSoftware
class VisibleSoftwareAdmin(ImportExportModelAdmin): resource_class = VisibleSoftwareResource

# Admin definitions for submission_info module ---------------------------------

class SubmissionInfoResource(resources.ModelResource):
	class Meta: model = SubmissionInfo
class SubmissionInfoAdmin(HSSIModelAdmin): resource_class = SubmissionInfoResource