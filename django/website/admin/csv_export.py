import os, re, traceback
import tablib

from import_export import resources
from ..models import *

from typing import Type, TYPE_CHECKING
if TYPE_CHECKING:
	from django.db import models
	from import_export import declarative

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
		Image,
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
		VisibleSoftware,
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
	export_model_csv(Image)
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
	export_model_csv(VisibleSoftware)
	export_model_csv(Region)
	export_model_csv(RepoStatus)
	export_model_csv(DataInput)
	export_model_csv(FileFormat)
	export_model_csv(SoftwareVersion)
	export_model_csv(Submitter)
	export_model_csv(RelatedItem)
	export_model_csv(SoftwareEditQueue)

	authors_field: SortedManyToManyField = Software._meta.get_field('authors').remote_field
	author_order = authors_field.through
	export_model_csv(author_order)

def import_model_csv(model: 'Type[models.Model]', filepath: os.PathLike | None = None):
	if filepath is None: filepath = model_csv_filepath(model)
	print(f"Importing {filepath} ...")

	if os.path.isfile(filepath):
		model_resource = resources.modelresource_factory(model)()
		try:
			dataset = tablib.Dataset().load(open(filepath).read(), format='csv')
			result = model_resource.import_data(dataset)

			if result.has_errors() or result.has_validation_errors():
				print("Import failed: ")
				print(
					f"Has errors: {str(result.has_errors())} " + 
					f"Has validation errors: {str(result.has_validation_errors())}"
				)
		
		except: traceback.print_exc()
	else: print(filepath + " does not exist, skipping")

def import_db_csv():
	# import order matters (?)
	import_model_csv(Image)
	import_model_csv(Organization)
	import_model_csv(Person)
	import_model_csv(Curator)
	import_model_csv(Award)
	import_model_csv(CpuArchitecture)
	import_model_csv(FunctionCategory)
	import_model_csv(InstrumentObservatory)
	import_model_csv(Keyword)
	import_model_csv(License)
	import_model_csv(OperatingSystem)
	import_model_csv(Phenomena)
	import_model_csv(ProgrammingLanguage)
	import_model_csv(Region)
	import_model_csv(RepoStatus)
	import_model_csv(DataInput)
	import_model_csv(FileFormat)
	import_model_csv(SoftwareVersion)
	import_model_csv(RelatedItem)
	import_model_csv(Submitter)
	import_model_csv(SubmissionInfo)
	import_model_csv(Software)
	import_model_csv(VisibleSoftware)
	import_model_csv(SoftwareEditQueue)

	authors_field: SortedManyToManyField = Software._meta.get_field('authors').remote_field
	author_order = authors_field.through
	import_model_csv(author_order)