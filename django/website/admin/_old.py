import os, uuid

from django import forms
from django.apps import apps
from django.conf import settings
from django.contrib import admin
from django.db import models
from django.db.models import QuerySet
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

#Libraries and code for sending queries to ADS and checking bibcodes
import json
from django.conf import settings
from django.core.mail import send_mail

from import_export import resources
from import_export.admin import ImportExportModelAdmin

from ..util import * 
from ..models import *
from ..views import migrate_db_old_to_new
from .csv_export import export_db_csv, import_db_csv, remove_all_model_entries
from .parse_ttl import parse_ttl
from .fetch_vocab import (
	DataListConcept, link_concept_children, get_data, get_concepts, 
	MODEL_URL_MAP, URL_FUNCTIONCATEGORIES
)

from django.db.models import F

## HSSI Admin Site
from django.http import HttpResponse, HttpRequest
from django.shortcuts import redirect
from ..metadata import get_metadata

from django.core.management import call_command
from django.contrib import admin
from django.urls import path

class HssiAdminSite(admin.AdminSite):
	site_title = 'HSSI admin'
	site_header = 'HSSI administration'
	index_title = 'HSSI administration'
	index_template = 'admin/index.html'

	# override get_urls to add custom views
	def get_urls(self: 'HssiAdminSite'):

		# here we need to insert our custom urls after all of the default 
		# patterns EXCEPT FOR the last one. Which is the catch-all pattern 
		# that is used for debugging, this one we do not want to catch every 
		# web page before our custom patterns are compared against. 
		# NOTE this pattern is only included in debug builds but swapping the 
		# final pattern in release builds shouldn't cause any issues.. hopefully
		urls_base = super().get_urls()
		urls = urls_base[:-1] + [
			path('export_db_new/', view_export_db_new, name='export_db_new'),
			path('import_db_new/', view_import_db_new, name='import_db_new'),
			path('get_metadata/', view_get_metadata, name='get_metadata'),
			path('migrate_old_to_new/', migrate_db_old_to_new, name="migrate_old_to_new"),
			path('fetch_vocab/', fetch_vocab, name="fetch_vocab")
		] + urls_base[-1:]
		return urls

## HSSI Admin Views

def view_get_metadata(request: HttpRequest) -> HttpResponse:
	
	# get the repo url from the request
	url = request.GET.get("repo_url")
	if url is None:
		return HttpResponse("No URL provided", content_type="text/plain", status=400)
	
	# get the metadata from the URL as a json object and respond with it
	data = get_metadata(url)
	return HttpResponse(json.dumps(data.__dict__), content_type="application/json")

def view_export_db_new(request: HttpRequest) -> HttpResponse:

	# only allow post requests from super user to export the database
	if request.method == 'POST' and request.user.is_superuser:
		print("Exporting new database to csv files..")
		export_db_csv()
	
	# redirect to admin page
	return redirect('admin:index')

def view_import_db_new(request: HttpRequest) -> HttpResponse:

	# only allow post requests from super user to reimport the database
	if request.method == 'POST' and request.user.is_superuser:

		print("removing all data from hssi models..")
		remove_all_model_entries()
		print("Importing new database from csv files..")
		import_db_csv()
	
	# redirect to admin page
	return redirect('admin:index')

def fetch_vocab(request: HttpRequest) -> HttpResponse:
	if not request.user.is_superuser: return

	app_label = ControlledList._meta.app_label
	for model_name, url in MODEL_URL_MAP.items():
		print(f"fetching vocab for {model_name}..")

		concept_data = get_concepts(get_data(url))
		concepts = DataListConcept.from_concept_serialized(concept_data)
		model = apps.get_model(app_label, model_name)
		if not (issubclass(model, HssiModel)):
			raise Exception(f"{model.__name__} is not a HSSI model")

		# cache all objects that were here before storing any, so we can remove 
		# the old ones
		old_objs = [x for x in model.objects.all()]
		matched_old_objs: list[ControlledList] = []

		print(f"found {len(concepts)} vocab terms from {request.get_full_path()}")
		for concept in concepts:
			new_obj = concept.to_model_entry(model)
			matched_obj: HssiModel = None

			print(f"searching for old {new_obj.name} match..")

			# look for any remaining objects that match the newly pulled vocab 
			# term, and flag them for reference updating and removal
			for oldobj in old_objs:
				identmatch = False
				if isinstance(oldobj, ControlledList): 
					identmatch = oldobj.identifier == new_obj.identifier
				if identmatch or oldobj.name == new_obj.name:
					matched_obj = oldobj
					matched_old_objs.append(matched_obj)
					old_objs.remove(oldobj)
					break

			# if an old object that matches the new object is found, replace all
			# of the old object references with the new object
			if matched_obj:
				oldrefs = find_database_references(matched_obj)
				print(f"found match! replacing {len(oldrefs)} references..")
				for refobj, field in oldrefs:
					if isinstance(field, ManyToManyField):
						getattr(refobj, field.name).remove(matched_obj)
						getattr(refobj, field.name).add(new_obj)
					else: setattr(refobj, field.name, new_obj)
					print(f"updated field '{refobj.pk}:{field}'")

		# remove old entries that have been replaced with new vocab terms
		for old_obj in matched_old_objs: old_obj.delete()

		# mark any objects that did not get replaced with new terms as outdated
		for old_obj in old_objs: old_obj.name = old_obj.name + " (OUTDATED)"

		if issubclass(model, ControlledList):
			model.post_fetch()
	
	# function categories are handled differently because they have a more 
	# complicated structure
	parse_ttl(FunctionCategory, URL_FUNCTIONCATEGORIES)
	FunctionCategory.post_fetch()

	return redirect('admin:index')

site = HssiAdminSite()

## Admin Model Classes

class CategoryResource(resources.ModelResource):

	class Meta:
		model = Category

class CategoryAdmin(ImportExportModelAdmin):
	resource_class = CategoryResource

	def children_display(self, category):
		return ", ".join([child.name for child in category.children.all()])
	children_display.short_description = "Children"

class CollectionResource(resources.ModelResource):

	class Meta:
		model = Collection

class CollectionAdmin(ImportExportModelAdmin):
	resource_class = CollectionResource

class ToolTypeResource(resources.ModelResource):

	class Meta:
		model = ToolType

class ToolTypeAdmin(ImportExportModelAdmin):
	resource_class = ToolTypeResource

class FeedbackResource(resources.ModelResource):

	class Meta:
		model = Feedback

class FeedbackAdmin(ImportExportModelAdmin):

	resource_class =  FeedbackResource
	exclude = ['resource_id_temp']

	def resource_name(self, obj): 
		return obj.resource.name

	list_display = ('resource_name', 'provide_demo_video', 'provide_tutorial', 'provide_web_app', 'relate_a_resource', 'correction_needed', 'comments', 'feedback_date')

class NewsItemResource(resources.ModelResource):

	class Meta:
		model = NewsItem

class NewsItemAdmin(ImportExportModelAdmin):

	resource_class =  NewsItemResource
	exclude = ['published_on']

	list_display = ('title', 'status','published_on')
	list_filter = ("status",)
	search_fields = ['title', 'content']

	def get_form(self, request, obj=None, **kwargs):
		return super().get_form(request, obj, **kwargs)    

	def save_model(self, request, obj, form, change):
		if not settings.DB_IMPORT_IN_PROGRESS and obj.status == NewsItemStatus.PUBLISH.name:
			obj.published_on = timezone.now()
			super().save_model(request, obj, form, change)
		else:
			super().save_model(request, obj, form, change)

class ResourceResource(resources.ModelResource):

	class Meta:
		model = Resource

class InLitResourceResource(resources.ModelResource):

	class Meta:
		model = InLitResource

def empty_str(string: str | None) -> bool:
	return string is None or len(string) <= 0

def make_published(modeladmin, request, queryset):
	queryset.update(is_published=True)
	for resource in queryset:
		resource.save()
make_published.short_description = "Mark selected resources as published"

def make_not_published(modeladmin, request, queryset):
	queryset.update(is_published=False)
	for resource in queryset: resource.save()
make_not_published.short_description = "Mark selected resources as not published"

def update_submission(modeladmin, request, queryset):
	for resource in queryset:
		if resource.submission:
			resource.submission.update_from(resource, update_creation_date=True)
update_submission.short_description = "Update the submissions of selected resources"

def fill_forms_from_repo_url(
	_mdl: admin.ModelAdmin, 
	_req: HttpRequest, 
	queryset: QuerySet[Submission | Resource]
):
	for sub in queryset:

		# do nothing if no repo link
		if empty_str(sub.repo_url):
			continue
		
		print("searching for repo data at " + sub.repo_url)

		# do nothing if no data found from link
		data = get_metadata(sub.repo_url)
		if data is None:
			print("ERROR - unable to fetch repo data from " + sub.repo_url)
			continue

		print("found repo data!")

		# add fields if not specified
		if empty_str(sub.name) or sub.name == "_":
			sub.name = data.name
		
		if sub.creation_date is None:
			sub.creation_date = data.created_date

		if sub.update_date is None:
			sub.update_date = data.updated_date

		if empty_str(sub.description):
			sub.description = data.description
		
		if empty_str(sub.code_language):
			sub.code_language = str.join(", ", data.languages)
		
		if empty_str(sub.version):
			sub.version = data.version

		sub.save()
fill_forms_from_repo_url.short_description = "Fill other fields from repo URL specified"

def update_times_from_repo_url(
	_mdl: admin.ModelAdmin, 
	_req: HttpRequest, 
	queryset: QuerySet[Submission | Resource]
):
	for sub in queryset:

		# do nothing if no repo link
		if empty_str(sub.repo_url):
			continue
		
		print("searching for repo data at " + sub.repo_url)

		# do nothing if no data found from link
		data = get_metadata(sub.repo_url)
		if data is None:
			print("ERROR - unable to fetch repo data from " + sub.repo_url)
			continue

		print("found repo data!")

		print(f"times for {sub.name}: {data.created_date}, {data.updated_date}")
		sub.creation_date = data.created_date
		sub.update_date = data.updated_date
		sub.save()
update_times_from_repo_url.short_description = "Update timestamp fields from times found in repo"

# functions to dynamically generate admin actions
# to bulk add resources to resource (tool) types or collections

def make_add_to_tooltype_action(tooltype):
	def add_to_tooltype(modeladmin, request, queryset):
		""" queryset is the set of resources to add to the resource type.
		modeladmin and request are for backwards compatability
		"""
		for resource in queryset:
			resource.tool_types.add(tooltype)
	add_to_tooltype.short_description = f"Add selected tool(s) to the '{tooltype.name}' resource type."
	add_to_tooltype.__name__ = 'add_to_resource_type_{0}'.format(tooltype.id)
	return add_to_tooltype

def make_add_to_collection_action(collection):
	def add_to_collection(modeladmin, request, queryset):
		""" queryset is the set of resources to add to the collection.
		modeladmin and request are for backwards compatability
		"""
		for resource in queryset:
			resource.collections.add(collection)
			resource.save()
	add_to_collection.short_description = f"Add selected tool(s) to the '{collection.name}' collection."
	add_to_collection.__name__ = 'add_to_collection_{0}'.format(collection.id)
	return add_to_collection 

class ResourceAdmin(ImportExportModelAdmin):

	resource_class =  ResourceResource

	list_display = ('name', 'search_keywords', 'version', 'creation_date', 'is_published', 'creation_date')
	list_filter = ('categories', 'tool_types', 'collections', 'creation_date', 'creation_date', 'is_published')
	search_fields = ['search_keywords', 'name']

	actions = [fill_forms_from_repo_url, update_times_from_repo_url, update_submission, make_published, make_not_published]

	def get_actions(self, request):
		actions = super(ResourceAdmin, self).get_actions(request)
		for tooltype in ToolType.objects.all():
			action = make_add_to_tooltype_action(tooltype)
			actions[action.__name__] = (action,
										action.__name__,
										action.short_description)
		
		for collection in Collection.objects.all():
			action = make_add_to_collection_action(collection)
			actions[action.__name__] = (action,
										action.__name__,
										action.short_description)

		return actions
	

	def save_model(self, request, obj, form, change):

		# If any changes are made to the resource object, update the submission object
		if change:
			# This step is to update the submission from the current form rather than the current saved status of the resource object
			# This ensures that changes made to categories, collections, tool_types in this save get ported over to the submission too, otherwise they will be offset            
			copy_obj = form.save(commit=True)
			if obj.submission: obj.submission.update_from(copy_obj, update_creation_date=True)
			copy_obj.delete()
		
		super().save_model(request, obj, form, change)

		place_static_copy(obj.logo)

def upgrade_to_resource(modeladmin, request, queryset):
	"""
	Upgrade a queryset of `InLitResource` objects to full resources.
	"""
	submissions = [in_lit_resource.submission for in_lit_resource in queryset]
	make_resource(modeladmin,request,submissions)

class InLitResourceAdmin(ImportExportModelAdmin):

	resource_class =  InLitResourceResource

	list_display = ('name', 'search_keywords', 'version', 'creation_date', 'is_published', 'creation_date')
	list_filter = ('categories', 'tool_types', 'collections', 'creation_date', 'creation_date', 'is_published')
	search_fields = ['search_keywords', 'name']

	actions = [update_submission, make_published, make_not_published,upgrade_to_resource]
	

	def save_model(self, request, obj, form, change):

		# If any changes are made to the resource object, update the submission object
		if change:
			# This step is to update the submission from the current form rather than the current saved status of the resource object
			# This ensures that changes made to categories, collections, tool_types in this save get ported over to the submission too, otherwise they will be offset
			copy_obj = form.save(commit=True)
			if obj.submission: obj.submission.update_from(copy_obj, update_creation_date=True)
			copy_obj.delete()
		
		super().save_model(request, obj, form, change)

		place_static_copy(obj.logo)

class SubmissionResource(resources.ModelResource):

	class Meta:
		model = Submission

API_KEY = "ADS_DEVLOPER_TOKEN" #settings.ADS_DEV_KEY
def isInlit(submission):
	# if 'adsabs.harvard.edu' in submission.ads_abstract_link:
	#     opener = urllib.request.build_opener()
	#     raw = urllib.request.Request(submission.ads_abstract_link)
	#     rawLink = opener.open(raw)
	#     link = rawLink.geturl()
	#     link = urllib.parse.unquote(link)
	#     bibcode = link[link.index('.edu')+9:link.index('.edu')+28]
	#     exceptions = ['ascl', 'zndo', 'SPIE', 'ASPC', 'LPICo']
	#     for exception in exceptions:
	#         if exception in bibcode:
	#             return True
	#     # if 'arXiv' in bibcode:
	#     #     return False
	#     results = requests.get("https://api.adsabs.harvard.edu/v1/export/bibtex/"+bibcode,
	#                             headers={'Authorization': 'Bearer ' + API_KEY})#,timeout=120)
	#     if results.text[:8] == '@ARTICLE':
	#         return True
	return False

def mark_missing_info(modeladmin, request, queryset):
	queryset.update(status = SubmissionStatus.MISSING_INFO)
	for submission in queryset: submission.save()
mark_missing_info.short_description = "0) Mark selected submissions as new tools with missing info"

def mark_ready_for_first_contact(modeladmin, request, queryset):
	queryset.update(status = SubmissionStatus.FIRST_CONTACT)
	for submission in queryset: submission.save()
mark_ready_for_first_contact.short_description = "1) Mark selected submissions as ready for first contact"

def mark_contacted(modeladmin, request, queryset):
	queryset.update(date_contacted = timezone.now())
	queryset.update(status = SubmissionStatus.CONTACTED)    
	for submission in queryset: submission.save()
mark_contacted.short_description = "2) Mark selected submisions as successfully contacted"

def mark_paused(modeladmin, request, queryset):
	queryset.update(status = SubmissionStatus.TOOL_PAUSED)
	for submission in queryset: submission.save()
mark_paused.short_description = "3) Mark selected submissions as paused (check the submission notes)"

def mark_received(modeladmin, request, queryset):
	queryset.update(status = SubmissionStatus.RECEIVED)
	for submission in queryset: submission.save()
mark_received.short_description = "4) Mark selected submissions as received"

def mark_in_review(modeladmin, request, queryset):
	queryset.update(status = SubmissionStatus.IN_REVIEW)
	for submission in queryset: submission.save()
mark_in_review.short_description = "5) Mark selected submissions as in review (our end)"

def mark_accepted(modeladmin, request, queryset):
	queryset.update(status = SubmissionStatus.ACCEPTED)
	for submission in queryset: submission.save()
mark_accepted.short_description = "6) Mark selected submissions as in review (their end)"

def make_in_lit_resource(modeladmin, request, queryset):
	"""
	Create `InLitResource` objects from a queryset of submissions.
	"""
	for submission in queryset:
		submission:Submission
		submission.make_in_lit_resource()
make_in_lit_resource.short_description = "7b) Create new InLitResources based on the selected submissions"

def make_resource(modeladmin, request, queryset):
	for submission in queryset:
		submission:Submission # vscode likes annotations like this
		submission.make_resource()
make_resource.short_description = "7) Create new resources based on the selected submissions"

def mark_under_development(modeladmin, request, queryset):
	queryset.update(status = SubmissionStatus.UNDER_DEVELOPMENT)
	for submission in queryset: submission.save()
mark_under_development.short_description = "7a) Mark selected submission as Under Development (admin web tool creation)"

def update_resource(modeladmin, request, queryset):
	for submission in queryset:
		if hasattr(submission, "resource"):
			submission.resource.update_from(submission)
		elif hasattr(submission, "il_resource"):
			submission.il_resource.update_from(submission)

update_resource.short_description = "Update the resources (or in-lit resources) of selected submissions"

def mark_rejected_abandoned(modeladmin, request, queryset):
	queryset.update(status = SubmissionStatus.REJECTED_ABANDONED)
	for submission in queryset: submission.save()
mark_rejected_abandoned.short_description = "8) Mark selected submmisions as rejected/abandoned"

def mark_spam(modeladmin, request, queryset):
	queryset.update(status = SubmissionStatus.SPAM)
	for submission in queryset: submission.save()
mark_spam.short_description = "9) Mark selected submmisions as spam"

class SubmissionAdmin(ImportExportModelAdmin):

	resource_class =  SubmissionResource

	formfield_overrides = {
		models.ManyToManyField: {'widget': forms.CheckboxSelectMultiple},
	}

	list_display = ('name', 'status', 'creation_date', 'has_unsynced_changes', 'date_contacted', 'shepherd', 
					'id', 'creation_date', 'contact_count')
	list_filter = ('status', 'creation_date', 'has_unsynced_changes', 'shepherd', 'creation_date', 'date_contacted', 'categories', 
				   'tool_types', 'collections', 'contact_count')
	
	search_fields = ['search_keywords', 'name']

	actions = [
		fill_forms_from_repo_url, update_times_from_repo_url, mark_missing_info,
		mark_ready_for_first_contact, mark_contacted, mark_paused, mark_received, mark_in_review, mark_accepted, make_resource,
		mark_under_development,make_in_lit_resource, mark_rejected_abandoned, mark_spam, update_resource
	]

	def save_model(self, request, obj, form, change):

		if obj.id is None:
			obj.id = uuid.uuid4()

		obj.creation_date = timezone.now()
		obj.has_unsynced_changes = True if hasattr(obj, 'resource') or hasattr(obj, 'il_resource') else False
		
		super().save_model(request, obj, form, change)

class TeamMemberResource(resources.ModelResource):

	class Meta:
		model = TeamMember
	
class TeamMemberAdmin(ImportExportModelAdmin):

	resource_class =  TeamMemberResource
	exclude = ['previous_order']

	def get_actions(self, request):
		actions = super().get_actions(request)
		if 'delete_selected' in actions:
			del actions['delete_selected']
		return actions

# Register your models here.

from .model_admin import *

site.register(Software, admin_class=SoftwareAdmin)
site.register(SoftwareEditQueue, admin_class=SoftwareEditQueueAdmin)
site.register(FileFormat, admin_class=FileFormatAdmin)
site.register(ProgrammingLanguage, admin_class=ProgrammingLanguageAdmin)
site.register(VisibleSoftware, admin_class=VisibleSoftwareAdmin)
site.register(InReviewSoftware, admin_class=InReviewSoftwareAdmin)
site.register(InstrumentObservatory, admin_class=InstrumentObservatoryAdmin)
site.register(SoftwareVersion, admin_class=SoftwareVersionAdmin)
site.register(FunctionCategory, admin_class=FunctionCategoryAdmin)
site.register(Person, admin_class=PersonAdmin)
site.register(Curator, admin_class=CuratorAdmin)
site.register(Organization, admin_class=OrganizationAdmin)
site.register(License, admin_class=LicenseAdmin)
site.register(SubmissionInfo, admin_class=SubmissionInfoAdmin)
site.register(OperatingSystem, admin_class=OperatingSystemAdmin)
site.register(Phenomena, admin_class=PhenomenaTypeAdmin)
site.register(Keyword, admin_class=KeywordAdmin)
site.register(Award, admin_class=AwardAdmin)
site.register(Image, admin_class=ImageAdmin)
site.register(Region, admin_class=RegionAdmin)
site.register(RepoStatus, admin_class=RepoStatusAdmin)
site.register(DataInput, admin_class=DataInputAdmin)
site.register(Submitter, admin_class=SubmitterAdmin)
site.register(RelatedItem, admin_class=DatasetAdmin)

site.register(Category, admin_class=CategoryAdmin)
site.register(Collection, admin_class=CollectionAdmin)
site.register(Feedback, admin_class=FeedbackAdmin)
site.register(NewsItem, admin_class=NewsItemAdmin)
site.register(Resource, admin_class=ResourceAdmin)
site.register(InLitResource, admin_class=InLitResourceAdmin)
site.register(Submission, admin_class=SubmissionAdmin)
site.register(TeamMember, admin_class=TeamMemberAdmin)
site.register(ToolType, admin_class=ToolTypeAdmin)

DEFAULT_DB_CONFIG_PATH = '/django/website/config/db/'
CATEGORIES_FILE_NAME = 'categories.csv'
COLLECTIONS_FILE_NAME = 'collections.csv'
FEEDBACK_FILE_NAME = 'feedback.csv'
NEWS_FILE_NAME = 'news.csv'
RESOURCES_FILE_NAME = 'resources.csv'
IN_LIT_RESOURCES_FILE_NAME = 'in_lit_resources.csv'
SUBMISSIONS_FILE_NAME = 'submissions.csv'
TEAM_FILE_NAME = 'team.csv'
TOOL_TYPES_FILE_NAME = 'tool_types.csv'

def export_categories(**kwargs):

	db_config_path = DEFAULT_DB_CONFIG_PATH if not 'path' in kwargs or kwargs['path'] is None else kwargs['path'] 
	categories_file_path = db_config_path + CATEGORIES_FILE_NAME

	print("Exporting categories to " + categories_file_path + " ...")
	model_resource = resources.modelresource_factory(model=Category)()
	dataset = model_resource.export()
	if os.path.exists(categories_file_path): os.remove(categories_file_path)
	with open(categories_file_path, 'w') as dataset_file:
		dataset_file.write(dataset.csv)

def export_collections(**kwargs):

	db_config_path = DEFAULT_DB_CONFIG_PATH if not 'path' in kwargs or kwargs['path'] is None else kwargs['path'] 
	collections_file_path = db_config_path + COLLECTIONS_FILE_NAME

	print("Exporting collections to " + collections_file_path + " ...")
	model_resource = resources.modelresource_factory(model=Collection)()
	dataset = model_resource.export()
	if os.path.exists(collections_file_path): os.remove(collections_file_path)
	with open(collections_file_path, 'w') as dataset_file:
		dataset_file.write(dataset.csv)

def export_feedback(**kwargs):

	db_config_path = DEFAULT_DB_CONFIG_PATH if not 'path' in kwargs or kwargs['path'] is None else kwargs['path'] 
	feedback_file_path = db_config_path + FEEDBACK_FILE_NAME

	print("Exporting feedback to " + feedback_file_path + " ...")
	model_resource = resources.modelresource_factory(model=Feedback)()
	dataset = model_resource.export()
	if os.path.exists(feedback_file_path): os.remove(feedback_file_path)
	with open(feedback_file_path, 'w') as dataset_file:
		dataset_file.write(dataset.csv)

def export_news(**kwargs):

	db_config_path = DEFAULT_DB_CONFIG_PATH if not 'path' in kwargs or kwargs['path'] is None else kwargs['path'] 
	news_file_path = db_config_path + NEWS_FILE_NAME

	print("Exporting news items to " + news_file_path + " ...")
	model_resource = resources.modelresource_factory(model=NewsItem)()
	dataset = model_resource.export()
	if os.path.exists(news_file_path): os.remove(news_file_path)
	with open(news_file_path, 'w') as dataset_file:
		dataset_file.write(dataset.csv)


def export_resources(**kwargs):

	db_config_path = DEFAULT_DB_CONFIG_PATH if not 'path' in kwargs or kwargs['path'] is None else kwargs['path'] 
	resources_file_path = db_config_path + RESOURCES_FILE_NAME

	print("Exporting resources to " + resources_file_path + " ...")
	model_resource = resources.modelresource_factory(model=Resource)()
	dataset = model_resource.export()
	if os.path.exists(resources_file_path): os.remove(resources_file_path)
	with open(resources_file_path, 'w') as dataset_file:
		dataset_file.write(dataset.csv)

def export_inlitresources(**kwargs):
	db_config_path = DEFAULT_DB_CONFIG_PATH if not 'path' in kwargs or kwargs['path'] is None else kwargs['path'] 
	resources_file_path = db_config_path + IN_LIT_RESOURCES_FILE_NAME
	print("Exporting in-lit resources to " + resources_file_path + " ...")
	model_resource = resources.modelresource_factory(model=InLitResource)()
	dataset = model_resource.export()
	if os.path.exists(resources_file_path): os.remove(resources_file_path)
	with open(resources_file_path, 'w') as dataset_file:
		dataset_file.write(dataset.csv)

def export_submissions(**kwargs):

	db_config_path = DEFAULT_DB_CONFIG_PATH if not 'path' in kwargs or kwargs['path'] is None else kwargs['path'] 
	submissions_file_path = db_config_path + SUBMISSIONS_FILE_NAME

	print("Exporting submissions to " + submissions_file_path + " ...")
	model_resource = resources.modelresource_factory(model=Submission)()
	dataset = model_resource.export()
	if os.path.exists(submissions_file_path): os.remove(submissions_file_path)
	with open(submissions_file_path, 'w') as dataset_file:
		dataset_file.write(dataset.csv)


def export_team(**kwargs):

	db_config_path = DEFAULT_DB_CONFIG_PATH if not 'path' in kwargs or kwargs['path'] is None else kwargs['path'] 
	team_file_path = db_config_path + TEAM_FILE_NAME

	print("Exporting team to " + team_file_path + " ...")
	model_resource = resources.modelresource_factory(model=TeamMember)()
	dataset = model_resource.export()
	if os.path.exists(team_file_path): os.remove(team_file_path)
	with open(team_file_path, 'w') as dataset_file:
		dataset_file.write(dataset.csv)

def export_tool_types(**kwargs):

	db_config_path = DEFAULT_DB_CONFIG_PATH if not 'path' in kwargs or kwargs['path'] is None else kwargs['path'] 
	tool_types_file_path = db_config_path + TOOL_TYPES_FILE_NAME

	print("Exporting tool types to " + tool_types_file_path + " ...")
	model_resource = resources.modelresource_factory(model=ToolType)()
	dataset = model_resource.export()
	if os.path.exists(tool_types_file_path): os.remove(tool_types_file_path)
	with open(tool_types_file_path, 'w') as dataset_file:
		dataset_file.write(dataset.csv)

def export_database(**kwargs):

	export_categories(**kwargs)
	export_collections(**kwargs)
	export_feedback(**kwargs)
	export_news(**kwargs)
	export_resources(**kwargs)
	export_inlitresources(**kwargs)
	export_submissions(**kwargs)
	export_team(**kwargs)
	export_tool_types(**kwargs)

# Model event signals

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

@receiver([post_delete, post_save])
def export_database_changes(sender, **kwargs):

	if sender is Category:
		export_categories(**kwargs)
	elif sender is Collection:
		export_collections(**kwargs)
	elif sender is NewsItem:
		export_news(**kwargs)
	elif sender is Feedback:
		export_feedback(**kwargs) 
	elif sender is Resource:
		export_resources(**kwargs)
	elif sender is InLitResource:
		export_inlitresources(**kwargs)
	elif sender is Submission:        
		export_submissions(**kwargs)
	elif sender is TeamMember:
		export_team(**kwargs)
	elif sender is ToolType:
		export_tool_types(**kwargs)
