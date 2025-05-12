from import_export import resources
from import_export.admin import ImportExportModelAdmin

from ..models.people import Person, Curator
from ..models.software import Software, VisibleSoftware, SoftwareVersion
from ..models.submission_info import SubmissionInfo
from ..models.auxillary_info import Functionality, RelatedItem, Award
from ..models.roots import (
    FunctionCategory, OperatingSystem, Phenomena, Keyword, Image, 
    Organization, License, InstrumentObservatory, RepoStatus, DataInput,
    ProgrammingLanguage, FileFormat, Region
)

# Admin definitions for roots module -------------------------------------------

class OperatingSystemResource(resources.ModelResource):
    class Meta: model = OperatingSystem
class OperatingSystemAdmin(ImportExportModelAdmin): resource_class = OperatingSystemResource

class PhenomenaTypeResource(resources.ModelResource):
    class Meta: model = Phenomena
class PhenomenaTypeAdmin(ImportExportModelAdmin): resource_class = PhenomenaTypeResource

class KeywordResource(resources.ModelResource):
    class Meta: model = Keyword
class KeywordAdmin(ImportExportModelAdmin): resource_class = KeywordResource

class ImageResource(resources.ModelResource):
    class Meta: model = Image
class ImageAdmin(ImportExportModelAdmin): resource_class = ImageResource

class RegionResource(resources.ModelResource):
    class Meta: model = Region
class RegionAdmin(ImportExportModelAdmin): resource_class = RegionResource

class DataInputResource(resources.ModelResource):
    class Meta: model = DataInput
class DataInputAdmin(ImportExportModelAdmin): resource_class = DataInputResource

class RepoStatusResource(resources.ModelResource):
    class Meta: model = RepoStatus
class RepoStatusAdmin(ImportExportModelAdmin): resource_class = RepoStatusResource

class FunctionCategoryResource(resources.ModelResource):
    class Meta: model = FunctionCategory
class FunctionCategoryAdmin(ImportExportModelAdmin): resource_class = FunctionCategoryResource

class InstrumentObservatoryResource(resources.ModelResource):
    class Meta: model = InstrumentObservatory
class InstrumentObservatoryAdmin(ImportExportModelAdmin): resource_class = InstrumentObservatoryResource

class LicenseResource(resources.ModelResource):
    class Meta: model = License
class LicenseAdmin(ImportExportModelAdmin): resource_class = LicenseResource

class OrganizationResource(resources.ModelResource):
    class Meta: model = Organization
class OrganizationAdmin(ImportExportModelAdmin): resource_class = OrganizationResource

class FileFormatResource(resources.ModelResource):
    class Meta: model = FileFormat
class FileFormatAdmin(ImportExportModelAdmin): resource_class = FileFormatResource

class ProgrammingLanguageResource(resources.ModelResource):
    class Meta: model = ProgrammingLanguage
class ProgrammingLanguageAdmin(ImportExportModelAdmin): resource_class = ProgrammingLanguageResource

# Admin definitions for people module ------------------------------------------

class PersonResource(resources.ModelResource): 
    class Meta: model = Person
class PersonAdmin(ImportExportModelAdmin): resource_class = PersonResource

class CuratorResource(resources.ModelResource):
    class Meta: model = Curator
class CuratorAdmin(ImportExportModelAdmin): resource_class = CuratorResource

class SubmitterResource(resources.ModelResource):
    class Meta: model = Person
class SubmitterAdmin(ImportExportModelAdmin): resource_class = SubmitterResource

# Admin definitions for Auxillary Info -----------------------------------------

class AwardResource(resources.ModelResource):
    class Meta: model = Award
class AwardAdmin(ImportExportModelAdmin): resource_class = AwardResource

class FunctionalityResource(resources.ModelResource):
    class Meta: model = Functionality
class FunctionalityAdmin(ImportExportModelAdmin): resource_class = FunctionalityResource

class DatasetResource(resources.ModelResource):
    class Meta: model = RelatedItem
class DatasetAdmin(ImportExportModelAdmin): resource_class = DatasetResource

class SoftwareVersionResource(resources.ModelResource):
    class Meta: model = SoftwareVersion
class SoftwareVersionAdmin(ImportExportModelAdmin): resource_class = SoftwareVersionResource

# Admin definitions for software module ----------------------------------------

class SoftwareResource(resources.ModelResource):
    class Meta: model = Software
class SoftwareAdmin(ImportExportModelAdmin): resource_class = SoftwareResource

class VisibleSoftwareResource(resources.ModelResource):
    class Meta: model = VisibleSoftware
class VisibleSoftwareAdmin(ImportExportModelAdmin): resource_class = VisibleSoftwareResource

# Admin definitions for submission_info module ---------------------------------

class SubmissionInfoResource(resources.ModelResource):
    class Meta: model = SubmissionInfo
class SubmissionInfoAdmin(ImportExportModelAdmin): resource_class = SubmissionInfoResource