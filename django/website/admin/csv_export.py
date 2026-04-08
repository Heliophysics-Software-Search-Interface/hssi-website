import os, re, traceback
import tablib

from django.db import transaction
from import_export import resources
from ..models import *

from typing import Type, TYPE_CHECKING
if TYPE_CHECKING:
	from django.db import models

# Setup ------------------------------------------------------------------------

DEFAULT_DB_EXPORT_PATH = '/django/website/config/db/'

# Utility ----------------------------------------------------------------------

def camel_to_snake(name: str) -> str:
	s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
	return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def snake_to_camel(name: str) -> str:
	parts = name.split('_')
	return ''.join(word.capitalize() for word in parts)

def model_csv_filepath(
	model: 'Type[models.Model]', 
	directory: os.PathLike = DEFAULT_DB_EXPORT_PATH
) -> str:
	return directory + camel_to_snake(model.__name__) + '.csv'

# Module functionality ---------------------------------------------------------

def remove_all_model_entries():
	authors_field: SortedManyToManyField = Software._meta.get_field('authors').remote_field
	models: list[Model] = [
		Organization,
		Person,
		Curator,
		Award,
		CpuArchitecture,
		FunctionCategory,
		InstrumentObservatory,
		Keyword,
		License,
		OperatingSystem,
		Phenomena,
		ProgrammingLanguage,
		Region,
		RepoStatus,
		DataInput,
		FileFormat,
		SoftwareVersion,
		RelatedItem,
		Submitter,
		SubmissionInfo,
		Software,
		VerifiedSoftware,
		SoftwareEditQueue,
		authors_field.through,
	]
	models.reverse()
	for model in models: model.objects.all().delete()

def export_model_csv(model: 'Type[models.Model]', directory: str = DEFAULT_DB_EXPORT_PATH):
	filepath: str = model_csv_filepath(model, directory)
	print(f'Exporting {model.__name__} to ' + filepath + ' ...')

	model_resource: resources.ModelResource = resources.modelresource_factory(model)()
	dataset: tablib.Dataset = model_resource.export()

	if os.path.exists(filepath): os.remove(filepath)
	with open(filepath, 'w') as dataset_file:
		dataset_file.write(dataset.csv)

def export_db_csv():
	export_model_csv(Organization)
	export_model_csv(Person)
	export_model_csv(Curator)
	export_model_csv(Award)
	export_model_csv(CpuArchitecture)
	export_model_csv(FunctionCategory)
	export_model_csv(InstrumentObservatory)
	export_model_csv(Keyword)
	export_model_csv(License)
	export_model_csv(OperatingSystem)
	export_model_csv(Phenomena)
	export_model_csv(ProgrammingLanguage)
	export_model_csv(SubmissionInfo)
	export_model_csv(Software)
	export_model_csv(VerifiedSoftware)
	export_model_csv(Region)
	export_model_csv(RepoStatus)
	export_model_csv(DataInput)
	export_model_csv(FileFormat)
	export_model_csv(SoftwareVersion)
	export_model_csv(Submitter)
	export_model_csv(RelatedItem)
	export_model_csv(SoftwareEditQueue)

	# Export sorted m2m order
	author_order = Software._meta.get_field('authors').remote_field.through
	software_func_order = Software._meta.get_field('software_functionality').remote_field.through
	phenomena_order = Software._meta.get_field('related_phenomena').remote_field.through
	region_order = Software._meta.get_field('related_region').remote_field.through

	export_model_csv(author_order)
	export_model_csv(software_func_order)
	export_model_csv(phenomena_order)
	export_model_csv(region_order)

@transaction.atomic
def import_model_csv(
	model: 'Type[models.Model]', 
	filepath: os.PathLike | None = None, 
	exclude_fields: list[str] = [],
	two_passes: bool = False,
):
	if filepath is None: filepath = model_csv_filepath(model)
	print(f"Importing {filepath} ...")

	if os.path.isfile(filepath):
		model_resource_class = resources.modelresource_factory(model)
		
		# remove excluded fields from importing
		for excluded_field in exclude_fields:
			del model_resource_class.fields[excluded_field]
		model_resource = model_resource_class()

		try:
			dataset = tablib.Dataset().load(open(filepath).read(), format='csv')

			# initial data import from csv
			result1 = model_resource.import_data(dataset)

			# sometimes we need to double import to resolve models with 
			# self-referencing fields
			result2 = None
			if two_passes:
				result2 = model_resource.import_data(dataset)

			for result in [result1, result2]:
				if result is None: continue
				if result.has_errors() or result.has_validation_errors():
					print("Import failed: ")
					print(
						f"Has errors: {str(result.has_errors())} " + 
						f"Has validation errors: {str(result.has_validation_errors())}"
					)
					for err in result.row_errors():
						print(err)
					for invalid in result.invalid_rows:
						for field, errs in invalid.error_dict.items():
							for err in errs:
								print(field, err)
					raise Exception("Import error!!")
		
		except Exception as e:
			traceback.print_exc()
			raise e
	else: print(filepath + " does not exist, skipping")

def import_db_csv():
	# import order matters
	import_model_csv(Organization)
	import_model_csv(Person)
	import_model_csv(Curator)
	import_model_csv(Award)
	import_model_csv(CpuArchitecture)
	import_model_csv(FunctionCategory, two_passes=True)
	import_model_csv(InstrumentObservatory)
	import_model_csv(Keyword)
	import_model_csv(License)
	import_model_csv(OperatingSystem)
	import_model_csv(Phenomena, two_passes=True)
	import_model_csv(ProgrammingLanguage)
	import_model_csv(Region, two_passes=True)
	import_model_csv(RepoStatus)
	import_model_csv(DataInput)
	import_model_csv(FileFormat)
	import_model_csv(SoftwareVersion)
	import_model_csv(RelatedItem)
	import_model_csv(Submitter)
	import_model_csv(
		Software, 
		exclude_fields=[
			"authors", 
			"software_functionality",
			"related_phenomena",
			"related_region",
		]
	)
	import_model_csv(SubmissionInfo)
	import_model_csv(VerifiedSoftware)
	import_model_csv(SoftwareEditQueue)

	author_order = Software._meta.get_field('authors').remote_field.through
	software_func_order = Software._meta.get_field('software_functionality').remote_field.through
	phenomena_order = Software._meta.get_field('related_phenomena').remote_field.through
	region_order = Software._meta.get_field('related_region').remote_field.through

	import_model_csv(author_order)
	import_model_csv(software_func_order)
	import_model_csv(phenomena_order)
	import_model_csv(region_order)

	print("Finished Importing DB!")