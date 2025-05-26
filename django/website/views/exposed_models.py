from django.http import JsonResponse, HttpRequest
from ..forms import SubmissionForm
from ..models import (
    Keyword, OperatingSystem, Phenomena, RepoStatus, Image,
    ProgrammingLanguage, DataInput, FileFormat, Region,
    InstrumentObservatory, FunctionCategory, License, Organization,
    Person, Curator, Submitter, Award, Functionality, RelatedItem,
    SubmissionInfo, SoftwareVersion, Software,
)
from ..models.structurizer import ModelStructure

def get_model_structure(request: HttpRequest) -> JsonResponse:
    structures = { "ModelStructures": [
        ModelStructure.create(Keyword).serialized(),
        ModelStructure.create(OperatingSystem).serialized(),
        ModelStructure.create(Phenomena).serialized(),
        ModelStructure.create(RepoStatus).serialized(),
        ModelStructure.create(Image).serialized(),
        ModelStructure.create(ProgrammingLanguage).serialized(),
        ModelStructure.create(DataInput).serialized(),
        ModelStructure.create(FileFormat).serialized(),
        ModelStructure.create(Region).serialized(),
        ModelStructure.create(InstrumentObservatory).serialized(),
        ModelStructure.create(FunctionCategory).serialized(),
        ModelStructure.create(License).serialized(),
        ModelStructure.create(Organization).serialized(),
        ModelStructure.create(Person).serialized(),
        ModelStructure.create(Curator).serialized(),
        ModelStructure.create(Submitter).serialized(),
        ModelStructure.create(Award).serialized(),
        ModelStructure.create(Functionality).serialized(),
        ModelStructure.create(RelatedItem).serialized(),
        ModelStructure.create(SubmissionInfo).serialized(),
        ModelStructure.create(SoftwareVersion).serialized(),
        ModelStructure.create(Software).serialized(),
    ]}
    return JsonResponse(structures)