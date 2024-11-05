import os, re, shutil, uuid

from datetime import timedelta
from enum import Enum
# import numpy

from urllib.parse import urlencode, unquote, quote
import requests
from json import JSONDecodeError
import warnings
from datetime import date
import unicodedata

from django.conf import settings
from django.core.validators import MaxValueValidator
from django.db import connection, models
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User
import urllib.request, urllib.parse



# See: https://github.com/charettes/django-colorful
from colorful.fields import RGBColorField

class AbstractTag(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(unique=True, max_length=100)
    abbreviation = models.CharField(max_length=4,blank=True)
    theme_color = RGBColorField(default='#000000')
    text_color = RGBColorField(default='#ffffff')
    description = models.TextField(max_length=700, blank=True)
    children = models.ManyToManyField('self', symmetrical=False, blank=True, related_name="parents")

    class Meta:
        abstract = True
        ordering = ['name']

    def __str__(self):
        return self.name

    def has_parents(self):
        return self.parents.all().count() != 0

    def has_children(self):
        return self.children.all().count() != 0
    
    def get_curator_names(self):
        curator_names = self.curators.all().values_list('name', flat=True)
        for sub_tag in self.children.all():
            curator_names = curator_names.union(sub_tag.curators.all().values_list('name', flat=True))
        return ", ".join(curator_names)
    
    def get_curator_names_with_links(self):
        curators = self.curators.all()
        for sub_tag in self.children.all():
            curators = curators.union(sub_tag.curators.all())
        curator_strings = []
        for curator in curators:
            if curator.personal_url:
                curator_strings.append(f"<a href='{curator.personal_url}' target='_blank'>{curator.name}</a>")
            else:
                curator_strings.append(curator.name)
        return ", ".join(curator_strings)

class Category(AbstractTag):

    index = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = "categories"

class Collection(AbstractTag):

    name = models.CharField(unique=True, max_length=100)

    class Meta:
        ordering = ['name']

class ToolType(AbstractTag):

    name = models.CharField(unique=True, max_length=100)

    class Meta:
        ordering = ['name']

def resource_media_directory_path(instance, filename):
    # The named file will be uploaded to MEDIA_ROOT/resources/<instance.name>/<filename>
    # Any existing file with the same name at the same path will be overwritten
    safe_resource_name = re.sub('[^a-zA-Z0-9.\-_]', '_', instance.name)
    safe_file_name = re.sub('[^a-zA-Z0-9.\-_]', '_', filename)
    safe_file_path = os.path.join("resources", safe_resource_name, safe_file_name)
    try: os.remove(settings.MEDIA_ROOT + safe_file_path)
    except: pass
    return safe_file_path

def place_static_copy(image_file):
    if image_file.name:
        image_file_rel_path = image_file.name
        media_file_path = os.path.join(settings.MEDIA_ROOT, image_file_rel_path)
        if os.path.isfile(media_file_path):
            static_file_path = os.path.join(settings.STATIC_ROOT, "media", image_file_rel_path)
            static_dir_path = os.path.dirname(static_file_path)
            if not os.path.isdir(static_dir_path):
                os.makedirs(static_dir_path)
            shutil.copy(media_file_path, static_file_path)

def generateCitationId():
    today = date.today()
    yearMon = today.strftime("%y%m")
    return yearMon

def get_new_cid()->str:
    """
    Generate a new citation ID
    
    Returns:
        (str): The next available CID.
    """
    yearMon = generateCitationId()
    currentCitations = Resource.objects.filter(
                citation_id__startswith =f"{yearMon}-" 
            ).order_by("citation_id")
    if len(currentCitations) == 0:
        #first resource in this month so start with 001
        return f"{yearMon}-001"
    else:
        latest = currentCitations.last()
        highestNumber = int ( latest.citation_id.split("-")[1] )
        newCitationNumber = highestNumber + 1
        return f"{yearMon}-{newCitationNumber:03d}"


class AbstractResource(models.Model):

    help_texts = {
        'name': "The name of the resource (limited to 40 characters)",
        'subtitle': "A descriptive sub-title (e.g. “Bayesian Statistical Analysis for Transit Lightcurve Fitting”; limited to 100 characters)",
        'version': "The (optional) version number of the resource (name + version must be unique). Updated regularly for github resources with releases.",
        'credits': "The developer/researcher credits of the resource (e.g. “Smith, J. et al.” or “The COOL Team”; may contain HTML)",
        'description': "A description of the resource <strong>(may contain HTML; limited to 700 characters)</strong>",
        'concise_description': "A short (suggested 120 char. max.) descriptive sentence to be used in social media and search previews.",
        'code_languages':"A list of coding languages used by this tool, seperated by commas (ex: Python3, C, Fortran). If the tool is a website or catalog, or has no code to interact with, put N/A",
        'logo_image': "Upload an (optional) logo image for the resource (limited to 1MB)",
        'logo_link': "<strong> Add one link only - </strong>An (optional) link to be associated with the resource's logo",
        'categories': "The categories that are applicable to the resource",
        'collections': "The collections that are applicable to the resource",
        'tool_types': "The tool types that are applicable to the resource",
        'about_link': "<strong> Add one link only - </strong>An (optional) link to further information or README about the resource (not the original publication)",
        'ads_abstract_link': "<strong> Add one link only - </strong>An (optional) link to an ADS entry or other bibliographic location for the original publication of the resource; links to ADS libraries also supported",
        'jupyter_link':"<strong> Add one link only - </strong>An (optional) link to an interactive Jupyter Notebook tutorial on <a href='https://mybinder.org/' target='_blank' rel='noopener noreferrer'>MyBinder.org</a> or any similar resource",
        'download_link': "<strong> Add one link only - </strong>An (optional) link to downloadable source code and other resources; can be Github, Bitbucket, or any other online repository",
        'download_data_link': "<strong> Add one link only - </strong>An (optional) link to downloadable data and other resources; can be Github, Bitbucket, or any other online repository",
        'launch_link': "<strong> Add one link only - </strong>An (optional) link to a web-accessible interface for the resource",
        'demo_link':"<strong> Add one link only - </strong>An (optional) link to tutorial video for the resource",
        'discuss_link': "An (optional) link to a discussion site for the resource",
        'related_tool_string': "List any tools related to the resource in this submission, i.e. tools that this software has expanded on, tools built off of this software, or tools that work in tandem with this software",
        'SEEC_tool': "Check if the tool is related to SEEC",
        'search_keywords' : "Keywords to prioritize in search",
        'ascl_id' : "ASCL ID (YYMM.NNN)"
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(db_index=True, max_length=150, verbose_name="resource name", help_text=help_texts['name'])
    subtitle = models.CharField(blank=True, max_length=100, verbose_name="resource subtitle", help_text=help_texts['subtitle'])
    version = models.CharField(blank=True, max_length=20, help_text=help_texts['version'])
    creation_date = models.DateTimeField(default=timezone.now)
    last_modification_date = models.DateTimeField(default=timezone.now, verbose_name="last mod date")
    credits = models.CharField(blank=True, max_length=256, help_text=help_texts['credits'])
    description = models.TextField(blank=True, max_length=700, help_text=help_texts['description'])
    concise_description = models.CharField(blank=True, max_length=200, help_text=help_texts['concise_description'])
    code_languages = models.CharField(default="", blank=True, max_length=256, help_text=help_texts['code_languages'], verbose_name="Code language(s)")
    categories = models.ManyToManyField(Category, blank=True, related_name="+", help_text=help_texts['categories'])
    collections = models.ManyToManyField(Collection, blank=True, related_name="+", help_text=help_texts['collections'])
    tool_types = models.ManyToManyField(ToolType, blank=True, related_name="+", help_text=help_texts['tool_types'])
    logo_image = models.ImageField(upload_to=resource_media_directory_path, blank=True, help_text=help_texts['logo_image'])
    logo_link = models.URLField(blank=True, help_text=help_texts['logo_link'])
    about_link = models.URLField(blank=True, help_text=help_texts['about_link'])
    ads_abstract_link = models.URLField(blank=True, verbose_name ="ADS abstract/library link", help_text=help_texts['ads_abstract_link'])
    jupyter_link = models.URLField(blank=True, verbose_name = "Interactive jupyter notebook tutorial link", help_text=help_texts['jupyter_link'])
    download_link = models.URLField(blank=True, verbose_name = "Public source code download link", help_text=help_texts['download_link'])
    download_data_link = models.URLField(blank=True, verbose_name = "Public data download link", help_text=help_texts['download_data_link'])
    launch_link = models.URLField(blank=True, verbose_name = "Web Interface link", help_text=help_texts['launch_link'])
    demo_link = models.URLField(blank=True,verbose_name = "Demo video link", help_text=help_texts['demo_link'])
    discuss_link = models.URLField(blank=True, help_text=help_texts['discuss_link'])
    citation_count = models.IntegerField(default=None, null=True, editable=False, verbose_name ="citation count")
    related_tool_string = models.CharField(default="", blank=True, max_length=256, help_text=help_texts['related_tool_string'], verbose_name="Related Tool(s)")
    SEEC_tool = models.BooleanField(default=False, verbose_name="SEEC Related Tool", help_text=help_texts['SEEC_tool'])
    search_keywords = models.CharField(default="", blank=True, max_length=256, help_text=help_texts['search_keywords'], verbose_name="Search Keywords")
    ascl_id = models.CharField(default="",blank=True,max_length=8,help_text=help_texts['ascl_id'],verbose_name='ASCL ID')
    ascii_credits = models.CharField(blank=True, max_length=256)

    class Meta:
        abstract = True
        unique_together = ('name', 'version')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        nfkd_form = unicodedata.normalize('NFKD', self.credits)
        self.ascii_credits = u"".join([c for c in nfkd_form if not unicodedata.combining(c)])
        super().save(*args, **kwargs)
    
    def update_from(self, other:'AbstractResource', update_last_modification_date=False):

        self.name = other.name
        self.subtitle = other.subtitle
        self.version = other.version
        self.credits = other.credits
        self.description = other.description
        self.concise_description = other.concise_description
        self.code_languages = other.code_languages
        self.logo_image = other.logo_image
        if hasattr(self, "submission"):
            place_static_copy(self.logo_image)
        self.logo_link = other.logo_link
        self.about_link = other.about_link
        self.ads_abstract_link = other.ads_abstract_link
        self.demo_link = other.demo_link
        self.discuss_link = other.discuss_link
        self.download_link = other.download_link
        self.download_data_link = other.download_data_link
        self.jupyter_link = other.jupyter_link
        self.launch_link = other.launch_link
        self.citation_count = other.citation_count
        self.related_tool_string = other.related_tool_string
        self.SEEC_tool = other.SEEC_tool
        self.search_keywords = other.search_keywords
        self.ascl_id = other.ascl_id

        if update_last_modification_date:
            self.last_modification_date = timezone.now()

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
    
    def get_bibcode(self)->str:
        """
        Get bibcode from `self.ads_abstract_link`
        If link is a library or does not exist, return None.
        """
        ads_abs_link = unquote(self.ads_abstract_link) # url decode
        if 'adsabs.harvard.edu' in ads_abs_link:
            if 'libraries' in ads_abs_link:
                return None
            else:
                bibcode = re.findall(r'abs/([^/]+)', ads_abs_link)[0]
                return bibcode
        else:
            return None

    def update_ads_link(self)->None:
        """
        Ask ADS to resolve bibcode.
        Replace `self.ads_abstract_link` using new bibcode.
        """
        bibcode = self.get_bibcode()
        if bibcode is None:
            pass
        else:
            query = { # see https://github.com/adsabs/adsabs-dev-api/blob/master/API_documentation_Python/Search_API_Python.ipynb
                'q': '*:*',
                "fl": "bibcode, date",
                "sort": "date desc",
                    "rows": 20
            }
            encoded_query = urlencode(query)
            payload = f'bibcode\n{bibcode}'
            results = requests.post("https://api.adsabs.harvard.edu/v1/search/bigquery?{}".format(encoded_query), \
                        headers={'Authorization': 'Bearer ' + settings.ADS_DEV_KEY}, \
                        data=payload,timeout=30).json()
            try:
                docs = results['response']['docs']
            except KeyError as err:
                print(f"Could not find `results['response']['docs']` for Resource {self.name}")
                raise err
            if len(docs) != 1:
                msg = f'Bibcode resolver for Resource {self.name} unexpectedly returned {len(docs)} results! Bibcode {bibcode} was used.\n'
                msg += str(results)
                raise ValueError()
            doc = docs[0]
            returned_bibcode = doc['bibcode']
            new_ads_link = f'https://ui.adsabs.harvard.edu/abs/{returned_bibcode}/abstract'
            self.ads_abstract_link = new_ads_link
            self.save()
            if hasattr(self,'submission'):
                self.submission.ads_abstract_link = new_ads_link
                self.submission.save()

    def get_citation_count(self)->int:
        """
        Get `citation_count` using the ADS API.
        """
        ads_abs_link = unquote(self.ads_abstract_link) # url decode
        if 'adsabs.harvard.edu' in ads_abs_link:
            if 'libraries' in ads_abs_link:
                library_id = re.search("[A-z0-9-]+$", ads_abs_link).group()
                search_query = f'citations(docs(library/{library_id}))'
                query = {
                    'q':search_query,
                    "fl": "bibcode, date",
                    "sort": "date desc",
                    "rows": 20
                }
                encoded_query = urlencode(query)
                results = requests.get("https://api.adsabs.harvard.edu/v1/search/query?{}".format(encoded_query), \
                           headers={'Authorization': 'Bearer ' + settings.ADS_DEV_KEY},timeout=30).json()
                try:
                    total_citations = results['response']['numFound']
                except KeyError as err:
                    print(f"Could not find `results['response']['numFound']` for Resource {self.name}")
                    raise err
                return total_citations
            else:
                opener = urllib.request.build_opener()
                raw = urllib.request.Request(self.ads_abstract_link)
                rawLink = opener.open(raw)
                link = rawLink.geturl()
                link = urllib.parse.unquote(link)
                bibcode = link[link.index('.edu')+9:link.index('.edu')+28]
                search_query = f'citations(bibcode:{bibcode})'
                query = { # see https://github.com/adsabs/adsabs-dev-api/blob/master/API_documentation_Python/Search_API_Python.ipynb
                    'q': search_query,
                    "fl": "bibcode, date",
                    "sort": "date desc",
                     "rows": 20
                }
                encoded_query = urlencode(query)
                results = requests.get("https://api.adsabs.harvard.edu/v1/search/query?{}".format(encoded_query), \
                           headers={'Authorization': 'Bearer ' + settings.ADS_DEV_KEY},timeout=30).json()
                try:
                    citation_count = results['response']['numFound']
                    # print('citations:', citation_count)
                    # print(results)
                except KeyError as err:
                    print(f"Could not find `results['response']['numFound']` for Resource {self.name}")
                    raise err
                return citation_count         
        else: # no link to ADS -- do nothing
            return None
    def query_ascl_id(self):
        """
        There are a number of methods to match a resource to its ASCL entry.
        Here they are in order of preference:
        1. ADS bibcode `ascl.soft...`
        2. 'described_in' bibcode
        3. Source code download link
        4. Web app link
        5. About link
        6. Data download link
        7. Resource Name & 'used_in' bibcode
        8. Resource Name & human verification
        """
        def call_api(key,value):
            """
            `query_items` are tuples of (keyword,value) such as ('title','TidalPy')
            """
            encoded_query = urlencode({"q": f'{key}:"{value}"'})
            url = f'https://ascl.net/api/search/?{encoded_query}'
            results = requests.get(url,timeout=10)
            return results.json()
        # 1
        results = call_api('bibcode',self.get_bibcode())
        if len(results) == 1: return results[0]['ascl_id']
        # 2
        results = call_api('described_in',self.get_bibcode())
        if len(results) == 1: return results[0]['ascl_id']
        # 3
        results = call_api('site_list',self.download_link)
        if len(results) == 1: return results[0]['ascl_id']
        # 4
        results = call_api('site_list',self.launch_link)
        if len(results) == 1: return results[0]['ascl_id']
        # 5
        results = call_api('site_list',self.about_link)
        if len(results) == 1: return results[0]['ascl_id']
        # 6
        results = call_api('site_list',self.download_data_link)
        if len(results) == 1: return results[0]['ascl_id']
        # 7
        results = call_api('title',self.name)
        # validate somehow
        bibcode = self.get_bibcode()
        for result in results:
            if bibcode is not None:
                if bibcode in result['used_in']:
                    return result['ascl_id']
        if len(results) == 0: return "" # no match on ASCL
        else:
            # human validation
            msg = f'Incomplete validation for Resource {self.name}:\n{results}'
            print(msg)
            raise RuntimeError(msg)




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
    provide_tutorial = models.BooleanField(default=False, verbose_name="A Jupyter notebook or another hands-on tutorial would be helpful")
    provide_web_app = models.BooleanField(default=False, verbose_name="A web-accessible application would be helpful")
    relate_a_resource = models.BooleanField(default=False, verbose_name="There is another resource that should be linked as related to this one")
    correction_needed = models.BooleanField(default=False, verbose_name="There is something incorrect in the resource listing")
    comments = models.TextField(blank=True, max_length=1500, verbose_name="Related comments or additional suggestions:", help_text=help_texts['comments'])

    class Meta:
        ordering = ['-feedback_date']
        verbose_name_plural = "feedback"

class NewsItemStatus(Enum):
    DRAFT = 'Draft'
    PUBLISH = 'Publish'

class NewsItem(models.Model):

    STATUS_CHOICES = ((status.name, status.value) for status in NewsItemStatus)

    title = models.CharField(max_length=40)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts")
    content = models.TextField()
    tweet_content = models.TextField(max_length=180, blank=True)
    published_on = models.DateTimeField(null=True)
    status = models.CharField(choices=STATUS_CHOICES, default=NewsItemStatus.DRAFT.name, max_length=20)

    class Meta:
        ordering = ["-published_on"]

    def __str__(self):
        return self.title

class Resource(AbstractResource):

    help_texts = AbstractResource.help_texts.copy()
    help_texts.update({
        'github_release': "The current update note published on the resource.",
        'is_hosted': "Indicates whether the resource is hosted (executed) on EMAC servers",
        'is_published': "Indicates whether this is a published EMAC resource",
        'subdomain': "The EMAC subdomain of a hosted resource",
        'path': "The path (starting with /) of a hosted resource",
        'status_notes': "Any further information regarding this resource",
        'SEEC_tool': "Check if the tool is related to SEEC",
        'citation_id' : "DO NOT EDIT: Unique periodical citation ID. format: YYMM-000"
    })

    is_hosted = models.BooleanField(default=False, help_text=help_texts['is_hosted'])
    is_published = models.BooleanField(default=False, help_text=help_texts['is_published'])
    subdomain = models.CharField(blank=True, max_length=20, help_text=help_texts['subdomain'])
    path = models.CharField(blank=True, max_length=60, help_text=help_texts['path'])

    github_release = models.TextField(blank=True, help_text=help_texts['github_release'])
    status_notes = models.TextField(blank=True)
    submission = models.OneToOneField('Submission', on_delete=models.SET_NULL, null=True,related_name='resource')
    related_resources = models.ManyToManyField('self', blank=True)
    SEEC_tool = models.BooleanField(default=False, verbose_name="SEEC Related Tool", help_text=help_texts['SEEC_tool'])

    citation_id = models.CharField(blank=True, max_length=8, 
    #unique=True,  #### once the database is seeded with unique citation_ids we should set the field to unique
        help_text=help_texts['citation_id'] )

    def is_under_development(self):
        result = False
        if hasattr(self, 'submission') and self.submission is not None:
            result = self.submission.is_under_development()
        return result

    class Meta:
        ordering = ['name']
    
    def get_absolute_url(self):
        return f'{settings.EMAC_PROTOCOL}://{settings.EMAC_DOMAIN}?cid={self.citation_id}'
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)



class InLitResource(AbstractResource):
    help_texts = AbstractResource.help_texts.copy()
    help_texts.update({
        'is_published': "Indicates whether this is a published EMAC resource",
        'status_notes': "Any further information regarding this resource",
        'SEEC_tool': "Check if the tool is related to SEEC",
    })
    
    is_published = models.BooleanField(default=False, help_text=help_texts['is_published'])

    status_notes = models.TextField(blank=True)
    submission = models.OneToOneField('Submission', on_delete=models.SET_NULL, null=True,related_name='il_resource')
    SEEC_tool = models.BooleanField(default=False, verbose_name="SEEC Related Tool", help_text=help_texts['SEEC_tool'])
    
    def is_under_development(self):
        result = False
        if hasattr(self, 'submission') and self.submission is not None:
            result = self.submission.is_under_development()
        return result

    class Meta:
        ordering = ['name']
        
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
        

class SubmissionStatus(Enum):
    MISSING_INFO = '0) Proposed Tool w/ Missing Info'
    FIRST_CONTACT = '1) Ready for 1st Contact'
    CONTACTED = '2) Contacted'
    TOOL_PAUSED = '3) Tool Development is Paused (Check Submission Notes)'
    RECEIVED = '4) Received'
    IN_REVIEW = '5) In Review (Our End)'
    ACCEPTED = '6) In Review (Their End)'
    RESOURCE_CREATED = '7) Resource Created'
    UNDER_DEVELOPMENT = '7a) Web Tool Under Development'
    IN_LITERATURE = '7b) In Literature Resource Created'
    REJECTED_ABANDONED = '8) Rejected/Abandoned'
    SPAM = '9) Spam'

class Submission(AbstractResource):

    STATUS_CHOICES = ((status.name, status.value) for status in SubmissionStatus)

    help_texts = AbstractResource.help_texts.copy()
    help_texts.update({
        'other_category': "Suggest a category not listed here",
        'private_code/data_link':"<strong> Add one link only - </strong>If your resource is not publicly available and you would like EMAC to host it, please provide a (private) link to your source code",
        'host_app_on_emac': "Would you like your tool to be hosted/executed on an EMAC server?",
        'host_data_on_emac': "Would you like to store data/model output on a web-accessible EMAC server?",
        'make_web_interface': "Are you interested in a new web interface?",
        'submitter_first_name': "Please provide your first name",
        'submitter_last_name': "Please provide your last name",
        'submitter_email': "Please provide an email address at which the EMAC team can contact you",
        'submission_notes': "Any further information you would like to include with your submission",
        'github_release': "Release Message for the latest Github release (Automatically pulled, but can be edited before sending out an alert)",
        'SEEC_tool': "Check if the tool is related to SEEC",
        'contact_count': "Number of times the submitter has been contacted",
        'curator_lock': "Curator who has submitted edits for approval"
    })

    labels = {
        'categories': "Categories (check all that apply)",
        'collections': "Collections (check all that apply)",
        'tool_types': "Tool types (check all that apply)",
        'make_web_interface': "Interested in a new web interface?",
        'host_app_on_emac': "Host a web-accessible version on EMAC?",
        'host_data_on_emac': "Host data/model output on EMAC?",
    }

    id = models.UUIDField(primary_key=True, editable=False)
    other_category = models.CharField(blank=True, max_length=256, help_text=help_texts['other_category'])
    private_code_or_data_link = models.URLField(blank=True,verbose_name ="private code/data link", help_text=help_texts['private_code/data_link'])
    host_app_on_emac = models.BooleanField(default=False,verbose_name = "host web-app?", help_text=help_texts['host_app_on_emac'])
    host_data_on_emac = models.BooleanField(default=False, verbose_name ="host output?", help_text=help_texts['host_data_on_emac'])
    make_web_interface = models.BooleanField(default=False, verbose_name = "new web interface?", help_text=help_texts['make_web_interface'])
    submitter_first_name = models.CharField(blank=True, max_length=100, verbose_name="your first name", help_text=help_texts['submitter_first_name'])
    submitter_last_name = models.CharField(blank=True, max_length=100, verbose_name="your last name", help_text=help_texts['submitter_last_name'])
    submitter_email = models.EmailField(verbose_name="your email", help_text=help_texts['submitter_email'])
    submission_notes = models.TextField(blank=True, help_text=help_texts['submission_notes'])
    github_release = models.TextField(blank=True, help_text=help_texts['github_release'])

    submitter_ip_address = models.GenericIPAddressField(blank=True, null=True)
    status = models.CharField(choices=STATUS_CHOICES, default=SubmissionStatus.FIRST_CONTACT.name, max_length=100)
    status_notes = models.TextField(blank=True)
    shepherd = models.CharField(max_length=40, blank=True)
    date_contacted = models.DateField(null=True, blank=True, editable=True)
    has_unsynced_changes = models.BooleanField(default=False, verbose_name="out of sync")
    SEEC_tool = models.BooleanField(default=False, verbose_name="SEEC Related Tool", help_text=help_texts['SEEC_tool'])
    contact_count = models.IntegerField(default=0, help_text=[help_texts['contact_count']])
    curator_lock = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="locked by curator", help_text=help_texts['curator_lock'], related_name='locked_submissions')
    last_curated_date = models.DateField(null=True, blank=True)
    last_curated_by = models.CharField(blank=True, max_length=100)
    all_curators = models.ManyToManyField(User, blank=True, related_name='curated_submissions')

    def is_under_development(self):
        return self.status == SubmissionStatus.UNDER_DEVELOPMENT.name
    
    def detail_string(self):
        
        # duplicate key value violates unique constraint
        string_rep = f"Name: {str(self.name)} \
            \n Subtitle: {str(self.subtitle)} \
            \n Credits: {str(self.credits)} \
            \n Description: {str(self.description)} \
            \n Categories: { ', '.join([category.name for category in self.categories.all()])} \
            \n Collections: { ', '.join([collection.name for collection in self.collections.all()])} \
            \n Tool Types: { ', '.join([tool_type.name for tool_type in self.tool_types.all()])} \
            \n Code Language(s): {str(self.code_languages)} \
            \n Other Category: {str(self.other_category)} \
            \n Host a Web-Accessible Version on EMAC? {str(self.host_app_on_emac)} \
            \n Host Data/Model Output on EMAC? {str(self.host_data_on_emac)} \
            \n Interested in a New Web Interface? {str(self.make_web_interface)} \
            \n About Link: {str(self.about_link)} \
            \n ADS Abstract Link: {str(self.ads_abstract_link)} \
            \n Demo Link: {str(self.demo_link)} \
            \n Discuss Link: {str(self.discuss_link)} \
            \n Download Link: {str(self.download_link)} \
            \n Jupyter Link: {str(self.jupyter_link)} \
            \n Launch Link: {str(self.launch_link)} \
            \n Private Code/Data link: {str(self.private_code_or_data_link)} \
            \n Related Tools: {str(self.related_tool_string)} \
            \n Submitter First Name: {str(self.submitter_first_name)} \
            \n Submitter Last Name: {str(self.submitter_last_name)} \
            \n Submitter Email: {str(self.submitter_email)} \
            \n Submission Notes: {str(self.submission_notes)} \
            \n Github Release: {str(self.github_release)}"

        return string_rep

    def html_detail_string(self):

        html_string_rep = self.detail_string().replace("\n", "<br />")

        return html_string_rep

    class Meta:
        ordering = ['-creation_date']
    
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
            
        resource.citation_id = get_new_cid()
         
        resource.save()

        self.status = SubmissionStatus.RESOURCE_CREATED.name
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
        self.status = SubmissionStatus.IN_LITERATURE.name
        self.last_curated_by = ''
        self.last_curated_date = None
        self.curator_lock = None
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
            
    
            
class NotificationFrequency(Enum):
    IMMEDIATELY = 'Immediately'
    DAILY = 'Daily'
    WEEKLY = 'Weekly'
    PAUSED = 'Paused'
    
class Subscription(models.Model):

    NOTIFICATION_FREQUENCY_CHOICES = ((frequency.name, frequency.value) for frequency in NotificationFrequency)

    help_texts = {
        'categories': "Please select one or more categories to receive alerts about",
        'collections': "Please select one or more collections to receive alerts about",
        'daily_digest': "Would you like to receive alerts in a single, daily digest?",
        'subscriber_email': "Please provide an email address at which EMAC can alert you.",
        'notification_frequency': 'Choose to pause notifications or be contacted immediately, daily, or weekly when new tools are added to your selected categories.',
        'internal': 'Check to mark this as an internal (team member) subscription to allow notifications from Dev'
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    categories = models.ManyToManyField(Category, blank=True, related_name="subscriptions")
    collections = models.ManyToManyField(Collection, blank=True, related_name="subscriptions")
    creation_date = models.DateTimeField(default=timezone.now)
    last_notification_date = models.DateTimeField(default=timezone.now, verbose_name="last notification date")
    notification_frequency = models.CharField(choices=NOTIFICATION_FREQUENCY_CHOICES, default=NotificationFrequency.IMMEDIATELY.name, max_length=20, help_text=help_texts['notification_frequency'])
    subscriber_email = models.EmailField(blank=False, unique=True, verbose_name="your email", help_text=help_texts['subscriber_email'], error_messages={"unique":"A subscription already exists for this email address. Please update your existing subscription instead."})
    internal = models.BooleanField(default=False, verbose_name='is internal', help_text=help_texts['internal'])

    class Meta:
        ordering = ['-last_notification_date']

    def __str__(self):
        return self.subscriber_email

    def detail_string(self): # for new/edited subscriptions
        # duplicate key value violates unique constraint
        # string_rep = f"Categories: {', '.join([category.name for category in self.categories.all()])} \
        #     \n Notification Frequency: {str(self.notification_frequency)} \
        #     \n Subscriber Email: {str(self.subscriber_email)}"
        cat_string = f"{', '.join([category.name for category in self.categories.all()])}"
        freq_string = f"{str(self.notification_frequency)}"
        email_string = f"{str(self.subscriber_email)}"

        return cat_string, freq_string, email_string

    def html_detail_string(self): # for new/edited subscriptions
        # html_string_rep = self.detail_string().replace("\n", "<br />")
        cat_string, freq_string, email_string = self.detail_string()
        return cat_string, freq_string, email_string

    def clean(self, *args, **kwargs):

        if self.id is None: # If this is a new Submission, not an edit ...
            self.id = uuid.uuid4()

        super(Subscription, self).clean(*args, **kwargs)

    def save(self, *args, **kwargs):
            self.full_clean()
            super(Subscription, self).save(*args, **kwargs)

class PendingSubscriptionNotification(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    creation_date = models.DateTimeField(default=timezone.now)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name="subscription")
    resources = models.ManyToManyField(Resource, related_name="resources")
    
    def __str__(self) -> str:
        return self.subscription.subscriber_email
    
    def is_due(self):

        due_now = False

        if self.subscription.notification_frequency is not NotificationFrequency.PAUSED.name:
            due_now = self.subscription.notification_frequency == NotificationFrequency.IMMEDIATELY.name
            if not due_now:
                if self.subscription.notification_frequency == NotificationFrequency.DAILY.name:
                    due_now = timezone.now() >= self.subscription.last_notification_date + timedelta(days=1)
                else:
                    due_now = timezone.now() >= self.subscription.last_notification_date + timedelta(weeks=1)

        return due_now

    class Meta:
        ordering = ['-creation_date']

_STATIC_TEAM_MEMBER_IMAGE_DIR = os.path.join(settings.STATIC_ROOT, "media", "resources", "emac_team")

def num_team_members():

    if "website_teammember" in connection.introspection.table_names():
        return TeamMember.objects.count()
    else:
        return 0

class TeamMember(models.Model):

    help_texts = {
        'categories': "The categories that the person helped curate.",
        'collections': "The collections that the person heped curate.",
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(db_index=True, max_length=100)
    member_image = models.ImageField(upload_to=resource_media_directory_path, blank=True)
    description = models.TextField(max_length=700)
    personal_url = models.URLField(blank=True) 
    order = models.PositiveIntegerField(default=num_team_members, validators=[MaxValueValidator(num_team_members)])
    previous_order = models.IntegerField(default=-1)
    is_alumnus = models.BooleanField(default=False)
    is_curator = models.BooleanField(default=False)
    curator_account = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='team_member')
    collections = models.ManyToManyField(Collection, blank=True, related_name="curators", help_text=help_texts['collections'])
    categories = models.ManyToManyField(Category, blank=True, related_name="curators", help_text=help_texts['categories'])

    class Meta:
        ordering = ["order"]

    def save(self, *args, **kwargs): 
        
        # If present, move the TeamMember's image file from the MEDIA folder to STATIC for serving the image
        if self.member_image and os.path.isfile(self.member_image.path):
            shutil.move(self.member_image.path, _STATIC_TEAM_MEMBER_IMAGE_DIR)
            self.member_image = os.path.join("resources", "emac_team", os.path.basename(self.member_image.path))

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
