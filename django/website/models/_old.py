import os, re, shutil, uuid

from enum import Enum
# import numpy

import warnings
from datetime import date
import unicodedata

from django.conf import settings
from django.core.validators import MaxValueValidator
from django.db import connection, models
from django.utils import timezone
from django.conf import settings

# See: https://github.com/charettes/django-colorful
from colorful.fields import RGBColorField

from .submission_info import SubmissionStatusCode

class AbstractTag(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(unique=True, max_length=100)
    abbreviation = models.CharField(max_length=4,blank=True)
    theme_color = RGBColorField(default='#000000')
    text_color = RGBColorField(default='#ffffff')
    description = models.TextField(max_length=700, blank=True)
    children = models.ManyToManyField('self', symmetrical=False, blank=True, related_name="parents")

    class Meta:
        abstract: bool = True
        ordering: list[str] = ['name']

    def __str__(self):
        return self.name

    def has_parents(self):
        return self.parents.all().count() != 0

    def get_parent(self):
        if self.has_parents():
            return self.parents.all()[0]
        return None
    
    def has_children(self):
        return self.children.all().count() != 0

class Category(AbstractTag):

    index = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = "~Categories"

class Collection(AbstractTag):

    name = models.CharField(unique=True, max_length=100)

    class Meta:
        ordering = ['name']
        verbose_name_plural = "~Collections"

class ToolType(AbstractTag):

    name = models.CharField(unique=True, max_length=100)

    class Meta:
        ordering = ['name']
        verbose_name_plural = "~Tool types"

def resource_media_directory_path(instance: 'AbstractResource', filename: str) -> str:
    # The named file will be uploaded to MEDIA_ROOT/resources/<instance.name>/<filename>
    # Any existing file with the same name at the same path will be overwritten
    safe_resource_name = re.sub('[^a-zA-Z0-9.\-_]', '_', instance.name)
    safe_file_name = re.sub('[^a-zA-Z0-9.\-_]', '_', filename)
    safe_file_path = os.path.join("resources", safe_resource_name, safe_file_name)
    try: os.remove(settings.MEDIA_ROOT + safe_file_path)
    except: pass
    return safe_file_path

def place_static_copy(image_file: models.ImageField):
    if image_file.name:
        image_file_rel_path = image_file.name
        media_file_path = os.path.join(settings.MEDIA_ROOT, image_file_rel_path)
        if os.path.isfile(media_file_path):
            static_file_path = os.path.join(settings.STATIC_ROOT, "media", image_file_rel_path)
            static_dir_path = os.path.dirname(static_file_path)
            if not os.path.isdir(static_dir_path):
                os.makedirs(static_dir_path)
            shutil.copy(media_file_path, static_file_path)

def generateCitationId() -> str:
    today = date.today()
    yearMon = today.strftime("%y%m")
    return yearMon

class QualitySpec(models.IntegerChoices):
    GOOD = 3, "Good"
    PARTIALLY_MET = 2, "Partially Met"
    NEEDS_IMPROVEMENT = 1, "Needs Improvement"
    UNKNOWN = 0, "Unknown"

    def get_img_url(self):
        match self:
            case QualitySpec.GOOD:
                return "https://img.shields.io/badge/Good-brightgreen.svg"
            case QualitySpec.PARTIALLY_MET:
                return "https://img.shields.io/badge/Partially%20Met-orange.svg"
            case QualitySpec.NEEDS_IMPROVEMENT:
                return "https://img.shields.io/badge/Needs%20Improvement-red.svg"
            case QualitySpec.UNKNOWN:
                return "https://img.shields.io/badge/unknown-gray.svg"

class RecomendationSpec(models.IntegerChoices):
    MANDITORY = 3, "Manditory"
    RECOMMENDED = 2, "Recommended"
    OPTIONAL = 1, "Optional"
    UNKNOWN = 0, "Unknown"

class PackageTier(models.IntegerChoices):
    GOLD = 3, "Gold"
    SILVER = 2, "Silver"
    BRONZE = 1, "Bronze"
    NONE = 0, "None"

class SubmissionStatus(models.IntegerChoices):
    MISSING_INFO = 0, 'Proposed Tool w/ Missing Info'
    FIRST_CONTACT = 1,  'Ready for 1st Contact'
    CONTACTED = 2, 'Contacted'
    TOOL_PAUSED = 3, 'Tool Development is Paused (Check Submission Notes)'
    RECEIVED = 4, 'Received'
    IN_REVIEW = 5, 'In Review (Our End)'
    ACCEPTED = 6, 'In Review (Their End)'
    RESOURCE_CREATED = 7, 'Resource Created'
    UNDER_DEVELOPMENT = 8, 'Web Tool Under Development'
    IN_LITERATURE = 9, 'In Literature Resource Created'
    REJECTED_ABANDONED = 10, 'Rejected/Abandoned'
    SPAM = 11, 'Spam'

    def to_new_code(self) -> SubmissionStatusCode:
        match self:
            case SubmissionStatus.MISSING_INFO: return SubmissionStatusCode.PROPOSED_RESOURCE
            case SubmissionStatus.FIRST_CONTACT: return SubmissionStatusCode.READY_FOR_CONTACT
            case SubmissionStatus.CONTACTED: return SubmissionStatusCode.CONTACTED
            case SubmissionStatus.TOOL_PAUSED: return SubmissionStatusCode.RESOURCE_DEV_PAUSED
            case SubmissionStatus.RECEIVED: return SubmissionStatusCode.RECEIVED
            case SubmissionStatus.IN_REVIEW: return SubmissionStatusCode.IN_REVIEW_INTERNAL
            case SubmissionStatus.ACCEPTED: return SubmissionStatusCode.IN_REVIEW_EXTERNAL
            case SubmissionStatus.RESOURCE_CREATED: return SubmissionStatusCode.RESOURCE_CREATED
            case SubmissionStatus.UNDER_DEVELOPMENT: return SubmissionStatusCode.PROPOSED_RESOURCE
            case SubmissionStatus.IN_LITERATURE: return SubmissionStatusCode.PROPOSED_RESOURCE
            case SubmissionStatus.REJECTED_ABANDONED: return SubmissionStatusCode.REJECTED
            case SubmissionStatus.SPAM: return SubmissionStatusCode.SPAM

class AbstractResource(models.Model):

    help_texts = {
        'name': "The name of the resource (limited to 40 characters)",
        'description': "A description of the resource <strong>(may contain Markdown; limited to 700 characters)</strong>",
        'link_release': "<strong> Add one link only - </strong>An (optional) link to the latest release of the resource",
        'repo_url': "<strong> Add one link only - </strong> An (optional) link that points to the github, gitlab, or other public remote repository url for the software. This can also be a link to a binary/other download if source code is not available.",
        'docs_url': "<strong> Add one link only - </strong>An (optional) link to further information or README about the resource (not the original publication)",
        'website_url': "<strong> Add one link only - </strong>An (optional) link to a web-accessible interface for the resource",
        'author': "The developer/researcher credits of the resource (e.g. “Smith, J. et al.” or “The COOL Team”; may contain Markdown)",
        'version': "The (optional) version number of the resource (name + version must be unique). Updated regularly for github resources with releases.",
        
        'code_language':"The primary programming language that the tool is developed in (e.g. Python, R, IDL, etc.)",
        'categories': "The categories that are applicable to the resource",
        'collections': "The collections that are applicable to the resource",
        'tool_types': "The tool types that are applicable to the resource",
        'related_tools': "List any tools related to the resource in this submission, i.e. tools that this software has expanded on, tools built off of this software, or tools that work in tandem with this software",
        'logo': "Upload an (optional) logo image for the resource (limited to 1MB)",
        'logo_url': "<strong> Add one link only - </strong>A URL where the logo image can be fetched from (e.g. https://example.com/logo.png)",
        'search_keywords' : "Keywords to prioritize in search, seperated by ','"
        
        # 'subtitle': "A descriptive sub-title (e.g. “Bayesian Statistical Analysis for Transit Lightcurve Fitting”; limited to 100 characters)",
        # 'concise_description': "A short (suggested 120 char. max.) descriptive sentence to be used in social media and search previews.",
        # 'download_link': "<strong> Add one link only - </strong>An (optional) link to downloadable resources",
        # 'download_data_link': "<strong> Add one link only - </strong>An (optional) link to downloadable data and other resources",
        # 'demo_link':"<strong> Add one link only - </strong>An (optional) link to demo for the resource",
        # 'discuss_link': "An (optional) link to a discussion site for the resource",
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(db_index=True, max_length=150, verbose_name="resource name", help_text=help_texts['name'])
    description = models.TextField(blank=True, max_length=700, help_text=help_texts['description'])
    release_url = models.URLField(blank=True, verbose_name="Release URL", help_text=help_texts['link_release'])
    repo_url = models.URLField(blank=True, verbose_name="Repository URL", help_text=help_texts['repo_url'])
    docs_url = models.URLField(blank=True, verbose_name="Documentation URL", help_text=help_texts['docs_url'])
    website_url = models.URLField(blank=True, verbose_name = "Website URL", help_text=help_texts['website_url'])
    author = models.CharField(blank=True, verbose_name="Author(s)", max_length=256, help_text=help_texts['author'])
    version = models.CharField(blank=True, max_length=20, help_text=help_texts['version'])
    creation_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now, verbose_name="last mod date")
    license = models.CharField(blank=True, max_length=256, help_text="The license under which the software is distributed")

    code_language = models.CharField(default="", blank=True, max_length=256, help_text=help_texts['code_language'], verbose_name="Code language(s)")
    related_tools = models.CharField(default="", blank=True, max_length=256, help_text=help_texts['related_tools'], verbose_name="Related Tool(s)")
    logo = models.ImageField(upload_to=resource_media_directory_path, blank=True, help_text=help_texts['logo'])
    logo_url = models.URLField(blank=True, verbose_name="Logo (URL)", help_text=help_texts['logo_url'])
    categories = models.ManyToManyField(Category, blank=True, related_name="+", help_text=help_texts['categories'])
    collections = models.ManyToManyField(Collection, blank=True, related_name="+", help_text=help_texts['collections'])
    tool_types = models.ManyToManyField(ToolType, blank=True, related_name="+", help_text=help_texts['tool_types'])
    search_keywords = models.CharField(default="", blank=True, max_length=256, help_text=help_texts['search_keywords'], verbose_name="Search Keywords")

    # unnecessary:
    # subtitle = models.CharField(blank=True, max_length=100, verbose_name="resource subtitle", help_text=help_texts['subtitle'])
    # concise_description = models.CharField(blank=True, max_length=200, help_text=help_texts['concise_description'])
    # discuss_link = models.URLField(blank=True, help_text=help_texts['discuss_link'])
    # download_link = models.URLField(blank=True, verbose_name = "Public download link", help_text=help_texts['download_link'])
    # download_data_link = models.URLField(blank=True, verbose_name = "Public data download link", help_text=help_texts['download_data_link'])
    # demo_link = models.URLField(blank=True,verbose_name = "Demo video link", help_text=help_texts['demo_link'])
    # ascii_credits = models.CharField(blank=True, max_length=256)

    class Meta:
        abstract = True
        unique_together = ('name', 'version')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        nfkd_form = unicodedata.normalize('NFKD', self.author)

        super().save(*args, **kwargs)
    
    def update_from(self, other:'AbstractResource', update_creation_date: bool = False):

        self.name = other.name
        self.version = other.version
        self.author = other.author
        self.description = other.description
        self.code_language = other.code_language
        self.logo = other.logo
        if hasattr(self, "submission"):
            place_static_copy(self.logo)
        self.logo_url = other.logo_url
        self.docs_url = other.docs_url
        self.website_url = other.website_url
        self.related_tools = other.related_tools
        self.search_keywords = other.search_keywords

        if update_creation_date:
            self.update_date = timezone.now()

        if hasattr(self, 'has_unsynced_changes'):
            self.has_unsynced_changes = False

        if hasattr(other, 'has_unsynced_changes'):
            other.has_unsynced_changes = False
            other.save()

        # Relationships cannot be set on a Model that does not yet have a primary key, 
        # which for AbstractResources is generated when it is first saved. So:
        self.save()
        self.categories.set(other.categories.all())
        self.collections.set(other.collections.all())
        self.tool_types.set(other.tool_types.all())
        self.save()

class Resource(AbstractResource):

    help_texts = AbstractResource.help_texts.copy()
    help_texts.update({
        'is_published': "Indicates whether this is a published resource",
        'status_notes': "Any further information regarding this resource"
    })

    is_published = models.BooleanField(default=False, help_text=help_texts['is_published'])
    status_notes = models.TextField(blank=True)
    submission = models.OneToOneField('Submission', on_delete=models.SET_NULL, blank=True, null=True, related_name='resource')
    related_resources = models.ManyToManyField('self', blank=True)

    spec_community = models.IntegerField(choices=QualitySpec.choices, default=QualitySpec.UNKNOWN, verbose_name="community")
    spec_documentation = models.IntegerField(choices=QualitySpec.choices, default=QualitySpec.UNKNOWN, verbose_name="documentation")
    spec_testing = models.IntegerField(choices=QualitySpec.choices, default=QualitySpec.UNKNOWN, verbose_name="testing")
    spec_maturity = models.IntegerField(choices=QualitySpec.choices, default=QualitySpec.UNKNOWN, verbose_name="maturity")

    def is_under_development(self):
        result = False
        if hasattr(self, 'submission') and self.submission is not None:
            result = self.submission.is_under_development()
        return result

    class Meta:
        ordering = ['name']
        verbose_name_plural = "~Resources"
    
    def get_absolute_url(self):
        return f'{settings.SITE_PROTOCOL}://{settings.SITE_DOMAIN}?id={self.id}'
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

class InLitResource(AbstractResource):
    help_texts = AbstractResource.help_texts.copy()
    help_texts.update({
        'is_published': "Indicates whether this is a published resource",
        'status_notes': "Any further information regarding this resource"
    })
    
    is_published = models.BooleanField(default=False, help_text=help_texts['is_published'])

    status_notes = models.TextField(blank=True)
    submission = models.OneToOneField('Submission', on_delete=models.SET_NULL, null=True,related_name='il_resource')
    
    def is_under_development(self):
        result = False
        if hasattr(self, 'submission') and self.submission is not None:
            result = self.submission.is_under_development()
        return result

    class Meta:
        ordering = ['name']
        verbose_name_plural = "~In lit resources"
        
    def get_absolute_url(self):
        """
        There should be no url for this resource because it does not
        have a CID.

        Raises:
            NotImplementedError: This method is not implemented. It should not be implemented.
        """
        raise NotImplementedError('There should not be a url for `InLitResource` objects.')

    def upgrade_to_resource(self):
        """
        Upgrade from InLitResource to Resource
        """
        submission:Submission = self.submission
        submission.make_resource()
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

class Submission(AbstractResource):

    help_texts = AbstractResource.help_texts.copy()
    help_texts.update({
        'other_category': "Suggest a category not listed here",
        'submitter_contact': "Please provide a way that our team can contact you",
        'submission_notes': "Any further information you would like to include with your submission",
        'contact_count': "Number of times the submitter has been contacted"
    })

    labels = {
        'categories': "Categories (check all that apply)",
        'collections': "Collections (check all that apply)",
        'tool_types': "Tool types (check all that apply)"
    }

    id = models.UUIDField(primary_key=True, editable=False)
    other_category = models.CharField(blank=True, max_length=256, help_text=help_texts['other_category'])

    submitter_contact = models.CharField(blank=True, max_length=256, verbose_name="contact info", help_text=help_texts['submitter_contact'])
    submission_notes = models.TextField(blank=True, help_text=help_texts['submission_notes'])

    submitter_ip_address = models.GenericIPAddressField(blank=True, null=True)
    status = models.IntegerField(choices=SubmissionStatus.choices, default=SubmissionStatus.FIRST_CONTACT.label)
    status_notes = models.TextField(blank=True)
    shepherd = models.CharField(max_length=40, blank=True)
    date_contacted = models.DateField(null=True, blank=True, editable=True)
    has_unsynced_changes = models.BooleanField(default=False, verbose_name="out of sync")
    contact_count = models.IntegerField(default=0, help_text=[help_texts['contact_count']])

    def is_under_development(self):
        return self.status == SubmissionStatus.UNDER_DEVELOPMENT
    
    def detail_string(self):
        
        # duplicate key value violates unique constraint
        string_rep = f"Name: {str(self.name)} \
            \n Credits: {str(self.author)} \
            \n Description: {str(self.description)} \
            \n Categories: { ', '.join([category.name for category in self.categories.all()])} \
            \n Collections: { ', '.join([collection.name for collection in self.collections.all()])} \
            \n Tool Types: { ', '.join([tool_type.name for tool_type in self.tool_types.all()])} \
            \n Code Language(s): {str(self.code_language)} \
            \n Other Category: {str(self.other_category)} \
            \n About Link: {str(self.docs_url)} \
            \n Demo Link: {str(self.demo_link)} \
            \n Discuss Link: {str(self.discuss_link)} \
            \n Download Link: {str(self.download_link)} \
            \n Launch Link: {str(self.website_url)} \
            \n Related Tools: {str(self.related_tools)} \
            \n Submitter Contact Info: {str(self.submitter_contact)} \
            \n Submission Notes: {str(self.submission_notes)}"

        return string_rep

    def html_detail_string(self):

        html_string_rep = self.detail_string().replace("\n", "<br />")

        return html_string_rep

    class Meta:
        ordering = ['-creation_date']
        verbose_name_plural = "~Submissions"
    
    def clean(self, *args, **kwargs):

        if self.id is None: # If this is a new Submission, not an edit ...
            self.id = uuid.uuid4()

        super(Submission, self).clean(*args, **kwargs)

    def save(self, *args, **kwargs):
            self.full_clean()
            super(Submission, self).save(*args, **kwargs)
    
    def _make_resource(self):
        resource = Resource()
        resource.update_from(self)
        resource.submission = self
         
        resource.save()

        self.status = SubmissionStatus.RESOURCE_CREATED
        self.save()
    
    def make_resource(self):
        """
        Make a new resource from this submission.
        """
        if hasattr(self,'il_resource'):
            self.il_resource.delete()
        if not hasattr(self,'resource'):
            self._make_resource()
        else:
            warnings.warn('Tried to make a new Resource when one already exists. No action taken!',RuntimeWarning)
    
    def _make_in_lit_resource(self):
        in_lit_resource = InLitResource()
        in_lit_resource.update_from(self)
        in_lit_resource.submission = self
        
        in_lit_resource.save()
        self.status = SubmissionStatus.IN_LITERATURE
        self.save()
    
    def make_in_lit_resource(self):
        """
        Make a new InLitResource from this submission.
        """
        if hasattr(self,'resource'):
            msg = 'Tried to make an InLitResource when a Resource already exists. No action taken!'
            warnings.warn(msg,RuntimeWarning)
        elif hasattr(self,'il_resource'):
            msg = 'Tried to make an InLitResource when one already exists. No action taken!'
            warnings.warn(msg,RuntimeWarning)
        else:
            self._make_in_lit_resource()

class Feedback(models.Model):

    help_texts = {
        'comments': "Maximum 1500 characters.",
    }
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resource_id_temp = models.CharField(blank=True, max_length=32)
    resource = models.ForeignKey('Resource', blank=True, null=True, on_delete=models.CASCADE, related_name='feedback')
    feedback_date = models.DateTimeField(default=timezone.now)
    submitter_ip_address = models.GenericIPAddressField(blank=True, null=True)
    provide_demo_video = models.BooleanField(default=False, verbose_name="A demonstration video would be helpful")
    provide_tutorial = models.BooleanField(default=False, verbose_name="A hands-on tutorial would be helpful")
    provide_web_app = models.BooleanField(default=False, verbose_name="A web-accessible application would be helpful")
    relate_a_resource = models.BooleanField(default=False, verbose_name="There is another resource that should be linked as related to this one")
    correction_needed = models.BooleanField(default=False, verbose_name="There is something incorrect in the resource listing")
    comments = models.TextField(blank=True, max_length=1500, verbose_name="Related comments or additional suggestions:", help_text=help_texts['comments'])

    class Meta:
        ordering = ['-feedback_date']
        verbose_name_plural = "~Feedback"

class NewsItemStatus(Enum):
    DRAFT = 'Draft'
    PUBLISH = 'Publish'

class NewsItem(models.Model):

    STATUS_CHOICES = ((status.name, status.value) for status in NewsItemStatus)

    title = models.CharField(max_length=40)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts")
    content = models.TextField()
    published_on = models.DateTimeField(null=True)
    status = models.CharField(choices=STATUS_CHOICES, default=NewsItemStatus.DRAFT.name, max_length=20)

    class Meta:
        ordering = ["-published_on"]
        verbose_name_plural = "~News items"

    def __str__(self):
        return self.title


_STATIC_TEAM_MEMBER_IMAGE_DIR = os.path.join(settings.STATIC_ROOT, "media", "resources", "hssi_team")

def num_team_members():

    if "website_teammember" in connection.introspection.table_names():
        return TeamMember.objects.count()
    else:
        return 0

class TeamMember(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(db_index=True, max_length=100)
    member_image = models.ImageField(upload_to=resource_media_directory_path, blank=True)
    description = models.TextField(max_length=700)
    personal_url = models.URLField(blank=True) 
    order = models.PositiveIntegerField(default=num_team_members, validators=[MaxValueValidator(num_team_members)])
    previous_order = models.IntegerField(default=-1)
    is_alumnus = models.BooleanField(default=False)

    class Meta:
        ordering = ["order"]
        verbose_name_plural = "~Team members"

    def save(self, *args, **kwargs): 
        
        # If present, move the TeamMember's image file from the MEDIA folder to STATIC for serving the image
        if self.member_image and os.path.isfile(self.member_image.path):
            shutil.move(self.member_image.path, _STATIC_TEAM_MEMBER_IMAGE_DIR)
            self.member_image = os.path.join("resources", "hssi_team", os.path.basename(self.member_image.path))

        # If we're not currently importing the database, and the member order has changed...
        if not settings.DB_IMPORT_IN_PROGRESS and self.order != self.previous_order:

            # If the member is a new addition, we set its previous order to the number of members, and allow the below to adjust other orders as needed
            if self.previous_order == -1:
                self.previous_order = num_team_members()
            
            # If the order increased, we need to decrement the order of members between the previous position and the new position
            if self.order > self.previous_order:
                for member in TeamMember.objects.filter(order__range=(self.previous_order + 1, self.order)):
                    # Make sure not to decrement self
                    if member.pk != self.pk:
                        member.order -= 1
                        member.previous_order = member.order
                        member.save()
            # ... else if the order has decreased, increment all order values greater than or equal to the new order but less than the original order
            elif self.order < self.previous_order:
                for member in TeamMember.objects.filter(order__range=(self.order, self.previous_order - 1)):
                    # Make sure not to increment self
                    if member.pk != self.pk:
                        member.order += 1
                        member.previous_order = member.order
                        member.save()

            self.previous_order = self.order

        super().save(*args, **kwargs)

        # Guard against a gap if changing the order of an existing member to the number of members.
        if self.order == num_team_members() and TeamMember.objects.filter(order=num_team_members() - 1).first() is None:
            self.order -= 1
            self.previous_order = self.order
            super().save(*args, **kwargs)

    def delete(self, *args, **kwargs): 

        # If present, delete the member's image file
        if self.member_image is not None:
            member_image_path_abs = os.path.join(_STATIC_TEAM_MEMBER_IMAGE_DIR, os.path.basename(self.member_image.name))
            if os.path.isfile(member_image_path_abs):
                os.remove(member_image_path_abs)

            # Decrement all higher order numbers
            for member in TeamMember.objects.filter(order__gt=self.order):
                member.order -= 1
                member.previous_order = member.order
                member.save()

        super().delete(*args, **kwargs) 

    def __str__(self):
        return self.name
