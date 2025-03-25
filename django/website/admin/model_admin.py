from import_export import resources
from import_export.admin import ImportExportModelAdmin

from ..models.basics import OperatingSystem, PhenomenaType, Keyword, Award, Image
from ..models.functionality import Functionality, FunctionCategory
from ..models.ivoa_entry import IvoaEntry
from ..models.license import License
from ..models.organization import Organization
from ..models.person import Person, Curator
from ..models.software import Software, FileFormat, ProgrammingLanguage, VisibleSoftware
from ..models.submission_info import SubmissionInfo

# Admin definitions for basics module ------------------------------------------

class OperatingSystemResource(resources.ModelResource):
    class Meta: model = OperatingSystem
class OperatingSystemAdmin(ImportExportModelAdmin): resource_class = OperatingSystemResource

class PhenomenaTypeResource(resources.ModelResource):
    class Meta: model = PhenomenaType
class PhenomenaTypeAdmin(ImportExportModelAdmin): resource_class = PhenomenaTypeResource

class KeywordResource(resources.ModelResource):
    class Meta: model = Keyword
class KeywordAdmin(ImportExportModelAdmin): resource_class = KeywordResource

class AwardResource(resources.ModelResource):
    class Meta: model = Award
class AwardAdmin(ImportExportModelAdmin): resource_class = AwardResource

class ImageResource(resources.ModelResource):
    class Meta: model = Image
class ImageAdmin(ImportExportModelAdmin): resource_class = ImageResource

# Admin definitions for functionality module -----------------------------------

class FunctionalityResource(resources.ModelResource):
    class Meta: model = Functionality
class FunctionalityAdmin(ImportExportModelAdmin): resource_class = FunctionalityResource

class FunctionCategoryResource(resources.ModelResource):
    class Meta: model = FunctionCategory
class FunctionCategoryAdmin(ImportExportModelAdmin): resource_class = FunctionCategoryResource

# Admin definitions for ivoa_entry module --------------------------------------

class IvoaEntryResource(resources.ModelResource):
    class Meta: model = IvoaEntry
class IvoaEntryAdmin(ImportExportModelAdmin): resource_class = IvoaEntryResource

# Admin definitions for license module -----------------------------------------

class LicenseResource(resources.ModelResource):
    class Meta: model = License
class LicenseAdmin(ImportExportModelAdmin): resource_class = LicenseResource

# Admin definitions for organization module ------------------------------------

class OrganizationResource(resources.ModelResource):
    class Meta: model = Organization
class OrganizationAdmin(ImportExportModelAdmin): resource_class = OrganizationResource

# Admin definitions for person module ------------------------------------------

class PersonResource(resources.ModelResource): 
    class Meta: model = Person
class PersonAdmin(ImportExportModelAdmin): resource_class = PersonResource

class CuratorResource(resources.ModelResource):
    class Meta: model = Curator
class CuratorAdmin(ImportExportModelAdmin): resource_class = CuratorResource

# Admin definitions for software module ----------------------------------------

class SoftwareResource(resources.ModelResource):
    class Meta: model = Software
class SoftwareAdmin(ImportExportModelAdmin): resource_class = SoftwareResource

class FileFormatResource(resources.ModelResource):
    class Meta: model = FileFormat
class FileFormatAdmin(ImportExportModelAdmin): resource_class = FileFormatResource

class ProgrammingLanguageResource(resources.ModelResource):
    class Meta: model = ProgrammingLanguage
class ProgrammingLanguageAdmin(ImportExportModelAdmin): resource_class = ProgrammingLanguageResource

class VisibleSoftwareResource(resources.ModelResource):
    class Meta: model = VisibleSoftware
class VisibleSoftwareAdmin(ImportExportModelAdmin): resource_class = VisibleSoftwareResource

# Admin definitions for submission_info module ---------------------------------

class SubmissionInfoResource(resources.ModelResource):
    class Meta: model = SubmissionInfo
class SubmissionInfoAdmin(ImportExportModelAdmin): resource_class = SubmissionInfoResource