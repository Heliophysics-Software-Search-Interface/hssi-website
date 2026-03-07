"""
define actions for use in the adminisatration page by admin users to allow for 
bulk database interactions, third party api interaction, and other uses
"""

from django.apps import apps
from django.contrib import admin

from ..models import *
from ..metadata import get_metadata
from .csv_export import export_db_csv, import_db_csv, remove_all_model_entries
from .parse_ttl import parse_ttl
from .fetch_vocab import (
	DataListConcept, get_data, get_concepts,
	MODEL_URL_MAP, URL_FUNCTIONCATEGORIES, URL_REGIONS, URL_PHENOMENA
)

## HSSI Admin Site
from django.db.models import ManyToManyField
from django.http import HttpResponse, HttpRequest
from django.shortcuts import redirect
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
						# if it's a sorted m2m field, the sort_value must be 
						# preserved so we modify the through table directly
						if isinstance(field, SortedManyToManyField):
							sm2m_field: SortedManyToManyField = field
							through: type[Model] = (
								sm2m_field.through 
								if hasattr(sm2m_field, "through") else 
								sm2m_field.remote_field.through
							)
							matched_obj_field: str = matched_obj._meta.model_name.lower()
							kwargs = {
								refobj._meta.model_name.lower(): refobj.pk,
								matched_obj_field: matched_obj.pk
							}
							entry = through.objects.get(**kwargs)
							setattr(entry, matched_obj_field, new_obj)
							entry.save()
						else:
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
	
	parse_ttl(Region, URL_REGIONS, remove_old_isolated=False)
	Region.post_fetch()

	return redirect('admin:index')
