import os, re, traceback

from import_export import resources
from ..models import (
    Software, SubmissionInfo, Award, Curator, FunctionCategory, Functionality,
    IvoaEntry, Image, Keyword, License, OperatingSystem, Organization, Person,
    PhenomenaType, ProgrammingLanguage, VisibleSoftware
)

from typing import Type, TYPE_CHECKING
if TYPE_CHECKING:
    from django.db import models
    from import_export import declarative
    import tablib

# Setup ------------------------------------------------------------------------

DEFAULT_DB_EXPORT_PATH = '/django/website/config/db/'

# Utility ----------------------------------------------------------------------

def camel_to_snake(name: str) -> str:
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def snake_to_camel(name: str) -> str:
    parts = name.split('_')
    return ''.join(word.capitalize() for word in parts)


# Module functionality ---------------------------------------------------------

def export_model_csv(model: 'Type[models.Model]', directory: str = DEFAULT_DB_EXPORT_PATH):
    filename: str = camel_to_snake(model.__name__) + '.csv'
    filepath: str = directory + filename
    print(f'Exporting {model.__name__} to ' + filepath + ' ...')

    model_resource: resources.ModelResource = resources.modelresource_factory(model)()
    dataset: tablib.Dataset = model_resource.export()

    if os.path.exists(filepath): os.remove(filepath)
    with open(filepath, 'w') as dataset_file:
        dataset_file.write(dataset.csv)

def export_db_csv():
    export_model_csv(Software)
    export_model_csv(VisibleSoftware)
    export_model_csv(SubmissionInfo)
    export_model_csv(Award)
    export_model_csv(Curator)
    export_model_csv(FunctionCategory)
    export_model_csv(Functionality)
    export_model_csv(IvoaEntry)
    export_model_csv(Image)
    export_model_csv(Keyword)
    export_model_csv(License)
    export_model_csv(OperatingSystem)
    export_model_csv(Organization)
    export_model_csv(Person)
    export_model_csv(PhenomenaType)
    export_model_csv(ProgrammingLanguage)

def import_model_csv(model: 'type[models.Model]', filepath: os.PathLike):
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
    export_model_csv(Image)
    export_model_csv(Organization)
    export_model_csv(Person)
    export_model_csv(Curator)
    export_model_csv(Award)
    export_model_csv(FunctionCategory)
    export_model_csv(Functionality)
    export_model_csv(IvoaEntry)
    export_model_csv(Keyword)
    export_model_csv(License)
    export_model_csv(OperatingSystem)
    export_model_csv(PhenomenaType)
    export_model_csv(ProgrammingLanguage)
    export_model_csv(SubmissionInfo)
    export_model_csv(Software)
    export_model_csv(VisibleSoftware)