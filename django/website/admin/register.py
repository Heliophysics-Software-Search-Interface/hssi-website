from ..models import *
from .model_admin import *
from .hssi_admin_site import admin_site

# Register your models here.
admin_site.register(Software, admin_class=SoftwareAdmin)
admin_site.register(SoftwareEditQueue, admin_class=SoftwareEditQueueAdmin)
admin_site.register(FileFormat, admin_class=FileFormatAdmin)
admin_site.register(ProgrammingLanguage, admin_class=ProgrammingLanguageAdmin)
admin_site.register(VerifiedSoftware, admin_class=VerifiedSoftwareAdmin)
admin_site.register(InstrumentObservatory, admin_class=InstrumentObservatoryAdmin)
admin_site.register(SoftwareVersion, admin_class=SoftwareVersionAdmin)
admin_site.register(FunctionCategory, admin_class=FunctionCategoryAdmin)
admin_site.register(Person, admin_class=PersonAdmin)
admin_site.register(Curator, admin_class=CuratorAdmin)
admin_site.register(Organization, admin_class=OrganizationAdmin)
admin_site.register(License, admin_class=LicenseAdmin)
admin_site.register(SubmissionInfo, admin_class=SubmissionInfoAdmin)
admin_site.register(OperatingSystem, admin_class=OperatingSystemAdmin)
admin_site.register(CpuArchitecture, admin_class=CpuArchitectureAdmin)
admin_site.register(Phenomena, admin_class=PhenomenaTypeAdmin)
admin_site.register(Keyword, admin_class=KeywordAdmin)
admin_site.register(Award, admin_class=AwardAdmin)
admin_site.register(Region, admin_class=RegionAdmin)
admin_site.register(RepoStatus, admin_class=RepoStatusAdmin)
admin_site.register(DataInput, admin_class=DataInputAdmin)
admin_site.register(Submitter, admin_class=SubmitterAdmin)
admin_site.register(RelatedItem, admin_class=DatasetAdmin)
