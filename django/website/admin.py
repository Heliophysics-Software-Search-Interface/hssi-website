import os, shutil , uuid, time

from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import datetime, timedelta
from datetime import date as date_package
from django.core.mail import send_mail
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.template.loader import render_to_string


#Libraries and code for sending queries to ADS and checking bibcodes
import requests
import json
from django.conf import settings
API_KEY = settings.ADS_DEV_KEY
import urllib.request, urllib.parse

from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import (
    Category, Collection, Feedback, NewsItem, NewsItemStatus, 
    PendingSubscriptionNotification, Resource, Submission, SubmissionStatus, 
    Subscription, TeamMember, ToolType, InLitResource
)
from .constants import SaveType
from .models import place_static_copy
from . import submissions

from .subscriptions import resource_added_categories

from django.db.models import F

admin.site.site_title = 'EMAC admin'
admin.site.site_header = 'EMAC administration'
admin.site.index_title = 'EMAC administration'




class CategoryResource(resources.ModelResource):

    class Meta:
        model = Category

class CategoryAdmin(ImportExportModelAdmin):
    resource_class = CategoryResource

    def children_display(self, category):
        return ", ".join([child.name for child in category.children.all()])
    children_display.short_description = "Children"

class CollectionResource(resources.ModelResource):

    class Meta:
        model = Collection

class CollectionAdmin(ImportExportModelAdmin):
    resource_class = CollectionResource

class ToolTypeResource(resources.ModelResource):

    class Meta:
        model = ToolType

class ToolTypeAdmin(ImportExportModelAdmin):
    resource_class = ToolTypeResource

class CitationCountListFilter(admin.SimpleListFilter):
    title = _('citation count')
    parameter_name = 'citations'

    def lookups(self, request, model_admin):
        return (
            ('0', _('0-10')),
            ('1', _('11-25')),
            ('2', _('26-50')),
            ('3', _('51-100')),
            ('4', _('100+')),
        )

    def queryset(self, request, queryset):
        if self.value() == '0':
            return queryset.filter(citation_count__gte=0, citation_count__lte=10)

        if self.value() == '1':
            return queryset.filter(citation_count__gte=11, citation_count__lte=25)

        if self.value() == '2':
            return queryset.filter(citation_count__gte=26, citation_count__lte=50)

        if self.value() == '3':
            return queryset.filter(citation_count__gte=51, citation_count__lte=100)

        if self.value() == '4':
            return queryset.filter(citation_count__gte=101)

class FeedbackResource(resources.ModelResource):

    class Meta:
        model = Feedback

class FeedbackAdmin(ImportExportModelAdmin):

    resource_class =  FeedbackResource
    exclude = ['resource_id_temp']

    def resource_name(self, obj): 
        return obj.resource.name

    list_display = (
        'resource_name', 'provide_demo_video', 'provide_tutorial', 
        'provide_web_app', 'relate_a_resource', 'correction_needed', 
        'comments', 'feedback_date'
    )

class NewsItemResource(resources.ModelResource):

    class Meta:
        model = NewsItem

class NewsItemAdmin(ImportExportModelAdmin):

    resource_class =  NewsItemResource
    exclude = ['published_on']

    list_display = ('title', 'status','published_on')
    list_filter = ("status",)
    search_fields = ['title', 'content']

    def get_form(self, request, obj=None, **kwargs):

        kwargs['widgets'] = {
            'tweet_content': forms.Textarea(attrs={
                'placeholder': "Enter your tweet content here. " +
                "The title and URL of the news item will be added automatically."
            })
        }

        return super().get_form(request, obj, **kwargs)    

    def save_model(self, request, obj, form, change):

        # If we're not currently importing the database, and the news item 
        # status is publish, send a coresponding tweet to Twitter
        if not settings.DB_IMPORT_IN_PROGRESS and obj.status == NewsItemStatus.PUBLISH.name:
            obj.published_on = timezone.now()
        
        super().save_model(request, obj, form, change)

class PendingSubscriptionNotificationResource(resources.ModelResource):
    
    class Meta:
        model = PendingSubscriptionNotification

class PendingSubscriptionNotificationAdmin(ImportExportModelAdmin):

    resource_class = PendingSubscriptionNotificationResource

    list_display = ('creation_date', 'subscription', 'is_due', 'id')

    readonly_fields = ('is_due',)

    @admin.display(description='Is Due')
    def is_due(self, instance):
        return instance.is_due()

class ResourceResource(resources.ModelResource):

    class Meta:
        model = Resource

class InLitResourceResource(resources.ModelResource):

    class Meta:
        model = InLitResource

def make_published(modeladmin, request, queryset):
    queryset.update(is_published=True)
    for resource in queryset:
        resource.save()

        # only call the resource_added_categores function if it's an actual 
        # Resource and not an InLitResource
        if isinstance(resource, Resource):
            resource_added_categories(resource)

make_published.short_description = "Mark selected resources as published"

def make_not_published(modeladmin, request, queryset):
    queryset.update(is_published=False)
    for resource in queryset: resource.save()
make_not_published.short_description = "Mark selected resources as not published"

def update_submission(modeladmin, request, queryset):
    for resource in queryset:
        if resource.submission:
            resource.submission.update_from(resource, update_last_modification_date=True)
update_submission.short_description = "Update the submissions of selected resources"

# functions to dynamically generate admin actions
# to bulk add resources to resource (tool) types or collections

def make_add_to_tooltype_action(tooltype):
    def add_to_tooltype(modeladmin, request, queryset):
        """ queryset is the set of resources to add to the resource type.
        modeladmin and request are for backwards compatability
        """
        for resource in queryset:
            resource.tool_types.add(tooltype)
    add_to_tooltype.short_description = (
        f"Add selected tool(s) to the '{tooltype.name}' resource type."
    )
    add_to_tooltype.__name__ = 'add_to_resource_type_{0}'.format(tooltype.id)
    return add_to_tooltype

def make_add_to_collection_action(collection):
    def add_to_collection(modeladmin, request, queryset):
        """ queryset is the set of resources to add to the collection.
        modeladmin and request are for backwards compatability
        """
        for resource in queryset:
            resource.collections.add(collection)
            resource.save()
    add_to_collection.short_description = (
        f"Add selected tool(s) to the '{collection.name}' collection."
    )
    add_to_collection.__name__ = 'add_to_collection_{0}'.format(collection.id)
    return add_to_collection 

class ResourceAdmin(ImportExportModelAdmin):

    resource_class =  ResourceResource

    actions = [update_submission, make_published, make_not_published]
    exclude = ('ascii_credits',)
    search_fields = ['search_keywords', 'name']
    list_display = (
        'name', 'search_keywords', 'subtitle', 'version', 
        'last_modification_date', 'citation_count', 'is_published', 
        'creation_date'
    )
    list_filter = (
        'categories', 'tool_types', 'collections', 'last_modification_date', 
        'creation_date', CitationCountListFilter, 'is_published', 'is_hosted'
    )

    def get_actions(self, request):
        actions = super(ResourceAdmin, self).get_actions(request)
        for tooltype in ToolType.objects.all():
            action = make_add_to_tooltype_action(tooltype)
            actions[action.__name__] = (action,
                                        action.__name__,
                                        action.short_description)
        
        for collection in Collection.objects.all():
            action = make_add_to_collection_action(collection)
            actions[action.__name__] = (action,
                                        action.__name__,
                                        action.short_description)

        return actions
    

    def save_model(self, request, obj, form, change):

        # If any changes are made to the resource object, update the submission object.
        # This step is to update the submission from the current form 
        # rather than the current saved status of the resource object
        # This ensures that changes made to categories, collections, 
        # tool_types in this save get ported over to the submission too, 
        # otherwise they will be offset            
        if change:
            copy_obj = form.save(commit=True)
            obj.submission.update_from(copy_obj, update_last_modification_date=True)
            copy_obj.delete()
        
        super().save_model(request, obj, form, change)

        place_static_copy(obj.logo_image)

def upgrade_to_resource(modeladmin, request, queryset):
    """
    Upgrade a queryset of `InLitResource` objects to full resources.
    """
    submissions = [in_lit_resource.submission for in_lit_resource in queryset]
    make_resource(modeladmin,request,submissions)
        
        


class InLitResourceAdmin(ImportExportModelAdmin):

    resource_class =  InLitResourceResource

    actions = [update_submission, make_published, make_not_published,upgrade_to_resource]
    exclude = ('ascii_credits',)
    search_fields = ['search_keywords', 'name']
    list_display = (
        'name', 'search_keywords', 'subtitle', 'version', 'last_modification_date', 
        'citation_count', 'is_published', 'creation_date'
    )
    list_filter = (
        'categories', 'tool_types', 'collections', 'last_modification_date', 
        'creation_date', CitationCountListFilter, 'is_published'
    )

    # def get_actions(self, request):
    #     actions = super(InLitResourceResource, self).get_actions(request)
    #     for tooltype in ToolType.objects.all():
    #         action = make_add_to_tooltype_action(tooltype)
    #         actions[action.__name__] = (action,
    #                                     action.__name__,
    #                                     action.short_description)
        
    #     for collection in Collection.objects.all():
    #         action = make_add_to_collection_action(collection)
    #         actions[action.__name__] = (action,
    #                                     action.__name__,
    #                                     action.short_description)

    #     return actions
    

    def save_model(self, request, obj, form, change):

        # If any changes are made to the resource object, update the submission object
        # This step is to update the submission from the current form 
        # rather than the current saved status of the resource object
        # This ensures that changes made to categories, collections, 
        # tool_types in this save get ported over to the submission too, 
        # otherwise they will be offset
        if change:
            copy_obj = form.save(commit=True)
            obj.submission.update_from(copy_obj, update_last_modification_date=True)
            copy_obj.delete()
        
        super().save_model(request, obj, form, change)

        place_static_copy(obj.logo_image)

class SubmissionResource(resources.ModelResource):

    class Meta:
        model = Submission


def resend_receipt_email(modeladmin, request, queryset):
    for submission in queryset:
        submissions.submission_was_saved(submission)
resend_receipt_email.short_description = "Send the submission receipt email again"

def send_initial_recruitment_email(modeladmin, request, queryset):
    for submission in queryset:
        submissions.send_contact_email(submission, SaveType.FIRSTCONTACT)
    # Updates all of the "first contact" submissions to "successfully contacted" 
    # and increments contact_count
    queryset.update(
        status='CONTACTED', 
        contact_count=F('contact_count') + 1, 
        date_contacted=timezone.now()
    )
send_initial_recruitment_email.short_description = "Send Initial Recruitment Email: 1st Contact"

def send_followup_recruitment_email(modeladmin, request, queryset):
    for submission in queryset:
        submissions.send_contact_email(submission, SaveType.RECONTACT)
    # Updates the contacted_date of the previously contacted submissions and 
    # increments contact_count
    queryset.update(
        status='CONTACTED', 
        contact_count=F('contact_count') + 1, 
        date_contacted=timezone.now()
    )
send_followup_recruitment_email.short_description = (
    "Send Re-Contact Email: Previously Contacted Tools"
)

def send_final_recruitment_email(modeladmin, request, queryset):
    for submission in queryset:
        submissions.send_contact_email(submission, SaveType.FINALCONTACT)
    # Updates the contacted_date of the previously contacted submissions and 
    # increments contact_count
    queryset.update(
        status='REJECTED_ABANDONED', 
        contact_count=F('contact_count') + 1, 
        date_contacted=timezone.now()
    )
send_final_recruitment_email.short_description = (
    "Send Final Recruitment Email: Previously Contacted Tools"
)

def send_initial_inlit_email(modeladmin, request, queryset):
    for submission in queryset:
        submissions.send_contact_email(submission, SaveType.INITIALINLITCONTACT)
    # Updates the contacted_date of the previously contacted submissions and 
    # increments contact_count
    queryset.update(
        status='CONTACTED', 
        contact_count=F('contact_count') + 1, 
        date_contacted=timezone.now()
    )
send_initial_inlit_email.short_description = (
    "Send Initial Recruitment Email for In-Lit Resource: 1st Contact"
)

def send_followup_inlit_email(modeladmin, request, queryset):
    for submission in queryset:
        submissions.send_contact_email(submission, SaveType.SECONDINLITCONTACT)
    # Updates the contacted_date of the previously contacted submissions and 
    # increments contact_count
    queryset.update(
        status='CONTACTED', 
        contact_count=F('contact_count')+1, 
        date_contacted=timezone.now()
    )
send_followup_inlit_email.short_description = (
    "Send Followup Informational Email for In-Lit Resource: " + 
    "Previously Contacted Tools"
)

def send_final_inlit_email(modeladmin, request, queryset):
    for submission in queryset:
        submissions.send_contact_email(submission, SaveType.FINALINLITCONTACT)
    # Updates the contacted_date of the previously contacted submissions and 
    # increments contact_count
    queryset.update(
        status='REJECTED_ABANDONED', 
        contact_count=F('contact_count') + 1, 
        date_contacted=timezone.now()
    )
send_final_inlit_email.short_description = (
    "Send Final Informational Email for In-Lit Resource: " +
    "Previously Contacted Tools"
)

def isInlit(submission):
    if 'adsabs.harvard.edu' in submission.ads_abstract_link:
        opener = urllib.request.build_opener()
        raw = urllib.request.Request(submission.ads_abstract_link)
        rawLink = opener.open(raw)
        link = rawLink.geturl()
        link = urllib.parse.unquote(link)
        bibcode = link[link.index('.edu')+9:link.index('.edu')+28]
        exceptions = ['ascl', 'zndo', 'SPIE', 'ASPC', 'LPICo']
        for exception in exceptions:
            if exception in bibcode:
                return True
        # if 'arXiv' in bibcode:
        #     return False
        results = requests.get(
            "https://api.adsabs.harvard.edu/v1/export/bibtex/" + bibcode,
            headers={'Authorization': 'Bearer ' + API_KEY}
        ) #,timeout=120)
        if results.text[:8] == '@ARTICLE':
            return True
    return False

def send_test_email(content):
    send_mail(
        'Test email', print(content), 
        "REDACTED@nasa.gov", ["REDACTED@nasa.gov"]
    ) # JPR Redacted Oct. 2024

def send_submission_contact_email(modeladmin, request, queryset):
    for submission in queryset:
        if submission.status == SubmissionStatus.FIRST_CONTACT.name:
            if isInlit(submission):
                submissions.send_contact_email(
                    submission, 
                    SaveType.INITIALINLITCONTACT
                )
            else:
                submissions.send_contact_email(submission, SaveType.FIRSTCONTACT)
            
            # Updates the contacted_date of the contacted submissions and 
            # increments contact_count
            submission.status = SubmissionStatus.CONTACTED.name
            submission.contact_count += 1
            submission.date_contacted = timezone.now()
            submission.save()
        
        elif submission.status == SubmissionStatus.CONTACTED.name:
            if isInlit(submission):
                if submission.contact_count == 1:
                    submissions.send_contact_email(submission, SaveType.SECONDINLITCONTACT)
                    submission:Submission
                    submission.make_in_lit_resource()
                    submission.status = SubmissionStatus.IN_LITERATURE.name
                else:
                    submissions.send_contact_email(submission, SaveType.FINALINLITCONTACT)
                    submission:Submission
                    submission.make_in_lit_resource()
                    submission.status = SubmissionStatus.IN_LITERATURE.name
            else:
                if submission.contact_count == 1:
                    submissions.send_contact_email(submission, SaveType.RECONTACT)
                else:
                    submissions.send_contact_email(submission, SaveType.FINALCONTACT)
                    submission.status = SubmissionStatus.REJECTED_ABANDONED.name
                    submission.status_notes = (
                        "Rejected by the drop-down Contact action. The resource " +
                        "is not in the literature and the developer has been contacted " +
                        "at least 3 times.\n" + submission.status_notes
                    )
            submission.contact_count += 1
            submission.date_contacted = timezone.now()
            submission.save()

        elif (
            submission.status == SubmissionStatus.IN_LITERATURE.name and 
            submission.contact_count == 2
        ):
            submissions.send_contact_email(submission, SaveType.FINALINLITCONTACT)
            submission.contact_count += 1
            submission.date_contacted = timezone.now()
            submission.save()

send_submission_contact_email.short_description = "Send Contact Emails for the Selected Submissions"


def mark_missing_info(modeladmin, request, queryset):
    queryset.update(status = SubmissionStatus.MISSING_INFO.name)
    for submission in queryset: submission.save()
mark_missing_info.short_description = "0) Mark selected submissions as new tools with missing info"

def mark_ready_for_first_contact(modeladmin, request, queryset):
    queryset.update(status = SubmissionStatus.FIRST_CONTACT.name)
    for submission in queryset: submission.save()
mark_ready_for_first_contact.short_description = (
    "1) Mark selected submissions as ready for first contact"
)

def mark_contacted(modeladmin, request, queryset):
    queryset.update(date_contacted = timezone.now())
    queryset.update(status = SubmissionStatus.CONTACTED.name)    
    for submission in queryset: submission.save()
mark_contacted.short_description = "2) Mark selected submisions as successfully contacted"

def mark_paused(modeladmin, request, queryset):
    queryset.update(status = SubmissionStatus.TOOL_PAUSED.name)
    for submission in queryset: submission.save()
mark_paused.short_description = (
    "3) Mark selected submissions as paused (check the submission notes)"
)

def mark_received(modeladmin, request, queryset):
    queryset.update(status = SubmissionStatus.RECEIVED.name)
    for submission in queryset: submission.save()
mark_received.short_description = "4) Mark selected submissions as received"

def mark_in_review(modeladmin, request, queryset):
    queryset.update(status = SubmissionStatus.IN_REVIEW.name)
    for submission in queryset: submission.save()
mark_in_review.short_description = "5) Mark selected submissions as in review (our end)"

def mark_accepted(modeladmin, request, queryset):
    queryset.update(status = SubmissionStatus.ACCEPTED.name)
    for submission in queryset: submission.save()
mark_accepted.short_description = "6) Mark selected submissions as in review (their end)"


def make_in_lit_resource(modeladmin, request, queryset):
    """
    Create `InLitResource` objects from a queryset of submissions.
    """
    for submission in queryset:
        submission:Submission
        submission.make_in_lit_resource()

make_in_lit_resource.short_description = (
    "7b) Create new InLitResources based on the selected submissions"
)
            


def make_resource(modeladmin, request, queryset):
    for submission in queryset:
        submission:Submission # vscode likes annotations like this
        submission.make_resource()

make_resource.short_description = "7) Create new resources based on the selected submissions"

def mark_under_development(modeladmin, request, queryset):
    queryset.update(status = SubmissionStatus.UNDER_DEVELOPMENT.name)
    for submission in queryset: submission.save()
mark_under_development.short_description = (
    "7a) Mark selected submission as Under Development (EMAC admin web tool creation)"
)

def update_resource(modeladmin, request, queryset):
    for submission in queryset:
        if hasattr(submission, "resource"):
            submission.resource.update_from(submission)
        elif hasattr(submission, "il_resource"):
            submission.il_resource.update_from(submission)

        if (submission.curator_lock != None):
            submission.curator_lock = None
            submission.save()

update_resource.short_description = (
    "Update the resources (or in-lit resources) of selected submissions"
)

def mark_rejected_abandoned(modeladmin, request, queryset):
    queryset.update(status = SubmissionStatus.REJECTED_ABANDONED.name)
    for submission in queryset: submission.save()
mark_rejected_abandoned.short_description = "8) Mark selected submmisions as rejected/abandoned"

def mark_spam(modeladmin, request, queryset):
    queryset.update(status = SubmissionStatus.SPAM.name)
    for submission in queryset: submission.save()
mark_spam.short_description = "9) Mark selected submmisions as spam"

class SubmissionAdmin(ImportExportModelAdmin):

    resource_class =  SubmissionResource

    formfield_overrides = {
        models.ManyToManyField: {'widget': forms.CheckboxSelectMultiple},
    }

    list_display = (
        'name', 'status', 'last_modification_date', 'has_unsynced_changes', 
        'date_contacted', 'shepherd', 'id', 'creation_date', 'contact_count'
    )
    list_filter = (
        'status', 'last_modification_date', 'has_unsynced_changes', 'shepherd', 
        'creation_date', 'date_contacted', 'categories', 'tool_types', 
        'collections', 'host_app_on_emac', 'host_data_on_emac',
        'make_web_interface', 'contact_count'
    )
    search_fields = ['search_keywords', 'name']
    exclude = ('ascii_credits',)
    readonly_fields = ('last_curated_date', 'last_curated_by', 'all_curators')
    actions = [
        send_submission_contact_email, resend_receipt_email, mark_missing_info,
        mark_ready_for_first_contact, mark_contacted, mark_paused, mark_received, 
        mark_in_review, mark_accepted, make_resource, mark_under_development,
        make_in_lit_resource, mark_rejected_abandoned, mark_spam, update_resource
    ]

    # hide the extra controls by the curator_lock field
    # so you can't add, edit or delete user accounts
    # from the submission admin form
    def get_form(self, request, obj=None, **kwargs):
        form = super(SubmissionAdmin, self).get_form(request, obj, **kwargs)
        curator_field = form.base_fields['curator_lock']
        curator_field.widget.can_add_related = False
        curator_field.widget.can_change_related = False
        curator_field.widget.can_delete_related = False
        # all_curators = form.base_fields['all_curators']
        # all_curators.widget.can_add_related = False
        
        return form

    def save_model(self, request, obj, form, change):

        if obj.id is None:
            obj.id = uuid.uuid4()

        obj.last_modification_date = timezone.now()
        obj.has_unsynced_changes = (
            hasattr(obj, 'resource') or 
            hasattr(obj, 'il_resource')
        )
        
        super().save_model(request, obj, form, change)
    
class SubscriptionResource(resources.ModelResource):
    
    class Meta:
        model = Subscription

class SubscriptionAdmin(ImportExportModelAdmin):

    resource_class = SubscriptionResource

    formfield_overrides = {
        models.ManyToManyField: {'widget': forms.CheckboxSelectMultiple},
    }

    def resource_name(self, obj): 
        return obj.resource.name

    list_display = (
        'last_notification_date', 'notification_frequency','subscriber_email', 
        'creation_date', 'id'
    )
    list_filter = ('notification_frequency', 'categories',)

class TeamMemberResource(resources.ModelResource):
    class Meta:
        model = TeamMember
    
class TeamMemberAdmin(ImportExportModelAdmin):

    resource_class =  TeamMemberResource
    exclude = ['previous_order']

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
    
    # hide the extra controls by the curator_account field
    # so you can't add, edit or delete user accounts
    # from the team member admin form
    def get_form(self, request, obj=None, **kwargs):
        form = super(TeamMemberAdmin, self).get_form(request, obj, **kwargs)
        curator_account = form.base_fields['curator_account']
        curator_account.widget.can_add_related = False
        curator_account.widget.can_change_related = False
        curator_account.widget.can_delete_related = False
        return form


# curator user actions
#
def plain_curator_welcome_message(user):
    welcome_message = "Welcome to the EMAC Curators program!\n\n"
    welcome_message += f'Your EMAC curators account user name is: {user.username}' + "\n\n"
    welcome_message += f'The email address associated with this account is: {user.email}' + "\n\n"
    welcome_message += (
        "In order to get started, please set your password by going to the " +
        "EMAC Curators login page:\n\n"
    )
    welcome_message += f'{settings.EMAC_PROTOCOL}://{settings.EMAC_DOMAIN}/curators' + "\n\n"
    welcome_message += (
        "Click on the 'Set/Reset password' link, enter the email above, and " +
        "click to get a password reset email sent to you.\n\n"
    )
    welcome_message += (
        "Follow the instructions in the email to set your password. Then you " +
        "can log in and get started curating!\n\n"
    )
    welcome_message += "Thank you!"
    return welcome_message

def add_user_to_curators_group(user):
    curators = Group.objects.get(name='Curators')
    if curators:
        curators.user_set.add(user)

def reset_password_to_random(user):
    new_password = User.objects.make_random_password()
    user.set_password(new_password)
    user.save()

def is_valid_email(email):
    from django.core.exceptions import ValidationError
    from django.core.validators import validate_email
    try:
        validate_email(email)
        return True
    except ValidationError as e:
        print(f'Email validation error: {e}')
        return False

def send_curator_welcome_email(user, request):
    if is_valid_email(user.email):
        context = {
            'EMAC_PROTOCOL': settings.EMAC_PROTOCOL,
            'EMAC_DOMAIN': settings.EMAC_DOMAIN,
            'user': user
        }
        from_address = "REDACTED@nasa.gov" 
        plain_message = plain_curator_welcome_message(user)
        welcome_email_message = render_to_string('website/curator_welcome_email.html', context)
        send_mail(
            "Welcome, EMAC Curator!", 
            plain_message, from_address, 
            [str(user.email)], 
            fail_silently=False, 
            html_message=welcome_email_message
        )
    else:
        messages.warning(request, f'The email supplied for account "{user.username}" did not pass validation: {user.email}')

def make_team_member_for_user(user, request):
    if user.first_name and user.last_name:
        existing = TeamMember.objects.filter(Q(name__startswith=user.first_name) & Q(name__endswith=user.last_name))
        if existing.count() > 0:
            messages.warning(request, f'There is already a Team Member with name {user.first_name} {user.last_name}')
        else:
            TeamMember.objects.create(name=f"{user.first_name} {user.last_name}", is_curator=True, curator_account=user)
    else:
        messages.error(request, f'Account "{user.username}" did not have both first and last name set, could not create Team Member')

@admin.action(description="Make selected users Curators (group/password/email/team):")
def make_curators(modeladmin, request, queryset):
    for user in queryset:
        # don't let a failure for any one user stop the whole process
        try:
            add_user_to_curators_group(user)
            reset_password_to_random(user)
            send_curator_welcome_email(user, request)
            make_team_member_for_user(user, request)
        except Exception as ex:
            messages.error(request, f'Error processing user "{user.username}": {ex}')

@admin.action(description="- Add selected users to Curators group")
def add_users_to_curators(modeladmin, request, queryset):
    for user in queryset:
        # don't let a failure for any one user stop the whole process
        try:
            add_user_to_curators_group(user)
        except Exception as ex:
            messages.error(request, f'Error adding user "{user.username}" to Curators group: {ex}')

@admin.action(description="- Reset selected users passwords")
def reset_curators_passwords(modeladmin, request, queryset):
    for user in queryset:
        # don't let a failure for any one user stop the whole process
        try:
            reset_password_to_random(user)
        except Exception as ex:
            messages.error(request, f'Error resetting password for user "{user.username}": {ex}')

@admin.action(description="- Send selected users 'Welcome to Curators' email")
def send_users_welcome_email(modeladmin, request, queryset):
    for user in queryset:
        # don't let a failure for any one user stop the whole process
        try:
            send_curator_welcome_email(user, request)
        except Exception as ex:
            messages.error(request, f'Error sending welcome email to user "{user.username}": {ex}')

@admin.action(description="- Create 'Team Member' items for selected users")
def make_curator_team_member(modeladmin, request, queryset):
    for user in queryset:
        try:
            make_team_member_for_user(user, request)
        except Exception as ex:
            messages.error(request, f'Error creating Team Member for user "{user.username}": {ex}')

class UserAdmin(BaseUserAdmin):
    actions = [
        make_curators,
        add_users_to_curators,
        reset_curators_passwords,
        send_users_welcome_email,
        make_curator_team_member
    ]


# Register your models here.

admin.site.register(Category, admin_class=CategoryAdmin)
admin.site.register(Collection, admin_class=CollectionAdmin)
admin.site.register(Feedback, admin_class=FeedbackAdmin)
admin.site.register(NewsItem, admin_class=NewsItemAdmin)
admin.site.register(PendingSubscriptionNotification, admin_class=PendingSubscriptionNotificationAdmin)
admin.site.register(Resource, admin_class=ResourceAdmin)
admin.site.register(InLitResource, admin_class=InLitResourceAdmin)
admin.site.register(Subscription, admin_class=SubscriptionAdmin)
admin.site.register(Submission, admin_class=SubmissionAdmin)
admin.site.register(TeamMember, admin_class=TeamMemberAdmin)
admin.site.register(ToolType, admin_class=ToolTypeAdmin)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

DEFAULT_DB_CONFIG_PATH = '/django/website/config/db/'

CATEGORIES_FILE_NAME = 'categories.csv'
COLLECTIONS_FILE_NAME = 'collections.csv'
FEEDBACK_FILE_NAME = 'feedback.csv'
NEWS_FILE_NAME = 'news.csv'
PENDING_SUBSCRIPTION_NOTIFICATIONS_FILE_NAME = 'pending_subscription_notifications.csv'
RESOURCES_FILE_NAME = 'resources.csv'
IN_LIT_RESOURCES_FILE_NAME = 'in_lit_resources.csv'
SUBMISSIONS_FILE_NAME = 'submissions.csv'
SUBSCRIPTIONS_FILE_NAME = 'subscriptions.csv'
TEAM_FILE_NAME = 'team.csv'
TOOL_TYPES_FILE_NAME = 'tool_types.csv'

def export_categories(**kwargs):

    db_config_path = DEFAULT_DB_CONFIG_PATH if not 'path' in kwargs or kwargs['path'] is None else kwargs['path'] 
    categories_file_path = db_config_path + CATEGORIES_FILE_NAME

    print("Exporting categories to " + categories_file_path + " ...")
    model_resource = resources.modelresource_factory(model=Category)()
    dataset = model_resource.export()
    if os.path.exists(categories_file_path): os.remove(categories_file_path)
    with open(categories_file_path, 'w') as dataset_file:
        dataset_file.write(dataset.csv)

def export_collections(**kwargs):

    db_config_path = DEFAULT_DB_CONFIG_PATH if not 'path' in kwargs or kwargs['path'] is None else kwargs['path'] 
    collections_file_path = db_config_path + COLLECTIONS_FILE_NAME

    print("Exporting collections to " + collections_file_path + " ...")
    model_resource = resources.modelresource_factory(model=Collection)()
    dataset = model_resource.export()
    if os.path.exists(collections_file_path): os.remove(collections_file_path)
    with open(collections_file_path, 'w') as dataset_file:
        dataset_file.write(dataset.csv)

def export_feedback(**kwargs):

    db_config_path = DEFAULT_DB_CONFIG_PATH if not 'path' in kwargs or kwargs['path'] is None else kwargs['path'] 
    feedback_file_path = db_config_path + FEEDBACK_FILE_NAME

    print("Exporting feedback to " + feedback_file_path + " ...")
    model_resource = resources.modelresource_factory(model=Feedback)()
    dataset = model_resource.export()
    if os.path.exists(feedback_file_path): os.remove(feedback_file_path)
    with open(feedback_file_path, 'w') as dataset_file:
        dataset_file.write(dataset.csv)

def export_news(**kwargs):

    db_config_path = DEFAULT_DB_CONFIG_PATH if not 'path' in kwargs or kwargs['path'] is None else kwargs['path'] 
    news_file_path = db_config_path + NEWS_FILE_NAME

    print("Exporting news items to " + news_file_path + " ...")
    model_resource = resources.modelresource_factory(model=NewsItem)()
    dataset = model_resource.export()
    if os.path.exists(news_file_path): os.remove(news_file_path)
    with open(news_file_path, 'w') as dataset_file:
        dataset_file.write(dataset.csv)

def export_pending_subscription_notifications(**kwargs):

    db_config_path = DEFAULT_DB_CONFIG_PATH if not 'path' in kwargs or kwargs['path'] is None else kwargs['path'] 
    pending_subscription_notifications_file_path = db_config_path + PENDING_SUBSCRIPTION_NOTIFICATIONS_FILE_NAME

    print("Exporting pending subscription notifications to " + pending_subscription_notifications_file_path + " ...")
    model_resource = resources.modelresource_factory(model=PendingSubscriptionNotification)()
    dataset = model_resource.export()
    if os.path.exists(pending_subscription_notifications_file_path): os.remove(pending_subscription_notifications_file_path)
    with open(pending_subscription_notifications_file_path, 'w') as dataset_file:
        dataset_file.write(dataset.csv)

def export_resources(**kwargs):

    db_config_path = DEFAULT_DB_CONFIG_PATH if not 'path' in kwargs or kwargs['path'] is None else kwargs['path'] 
    resources_file_path = db_config_path + RESOURCES_FILE_NAME

    print("Exporting resources to " + resources_file_path + " ...")
    model_resource = resources.modelresource_factory(model=Resource)()
    dataset = model_resource.export()
    if os.path.exists(resources_file_path): os.remove(resources_file_path)
    with open(resources_file_path, 'w') as dataset_file:
        dataset_file.write(dataset.csv)

def export_inlitresources(**kwargs):
    db_config_path = DEFAULT_DB_CONFIG_PATH if not 'path' in kwargs or kwargs['path'] is None else kwargs['path'] 
    resources_file_path = db_config_path + IN_LIT_RESOURCES_FILE_NAME
    print("Exporting in-lit resources to " + resources_file_path + " ...")
    model_resource = resources.modelresource_factory(model=InLitResource)()
    dataset = model_resource.export()
    if os.path.exists(resources_file_path): os.remove(resources_file_path)
    with open(resources_file_path, 'w') as dataset_file:
        dataset_file.write(dataset.csv)

def export_submissions(**kwargs):

    db_config_path = DEFAULT_DB_CONFIG_PATH if not 'path' in kwargs or kwargs['path'] is None else kwargs['path'] 
    submissions_file_path = db_config_path + SUBMISSIONS_FILE_NAME

    print("Exporting submissions to " + submissions_file_path + " ...")
    model_resource = resources.modelresource_factory(model=Submission)()
    dataset = model_resource.export()
    if os.path.exists(submissions_file_path): os.remove(submissions_file_path)
    with open(submissions_file_path, 'w') as dataset_file:
        dataset_file.write(dataset.csv)
        
def export_subscriptions(**kwargs):

    db_config_path = DEFAULT_DB_CONFIG_PATH if not 'path' in kwargs or kwargs['path'] is None else kwargs['path'] 
    subscriptions_file_path = db_config_path + SUBSCRIPTIONS_FILE_NAME

    print("Exporting subscriptions to " + subscriptions_file_path + " ...")
    model_resource = resources.modelresource_factory(model=Subscription)()
    dataset = model_resource.export()
    if os.path.exists(subscriptions_file_path): os.remove(subscriptions_file_path)
    with open(subscriptions_file_path, 'w') as dataset_file:
        dataset_file.write(dataset.csv)

def export_team(**kwargs):

    db_config_path = DEFAULT_DB_CONFIG_PATH if not 'path' in kwargs or kwargs['path'] is None else kwargs['path'] 
    team_file_path = db_config_path + TEAM_FILE_NAME

    print("Exporting team to " + team_file_path + " ...")
    model_resource = resources.modelresource_factory(model=TeamMember)()
    dataset = model_resource.export()
    if os.path.exists(team_file_path): os.remove(team_file_path)
    with open(team_file_path, 'w') as dataset_file:
        dataset_file.write(dataset.csv)

def export_tool_types(**kwargs):

    db_config_path = DEFAULT_DB_CONFIG_PATH if not 'path' in kwargs or kwargs['path'] is None else kwargs['path'] 
    tool_types_file_path = db_config_path + TOOL_TYPES_FILE_NAME

    print("Exporting tool types to " + tool_types_file_path + " ...")
    model_resource = resources.modelresource_factory(model=ToolType)()
    dataset = model_resource.export()
    if os.path.exists(tool_types_file_path): os.remove(tool_types_file_path)
    with open(tool_types_file_path, 'w') as dataset_file:
        dataset_file.write(dataset.csv)

def export_database(**kwargs):

    export_categories(**kwargs)
    export_collections(**kwargs)
    export_feedback(**kwargs)
    export_news(**kwargs)
    export_pending_subscription_notifications(**kwargs)
    export_resources(**kwargs)
    export_inlitresources(**kwargs)
    export_submissions(**kwargs)
    export_subscriptions(**kwargs)
    export_team(**kwargs)
    export_tool_types(**kwargs)

# Model event signals

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

@receiver([post_delete, post_save])
def export_database_changes(sender, **kwargs):

    if sender is Category:
        export_categories(**kwargs)
    elif sender is Collection:
        export_collections(**kwargs)
    elif sender is NewsItem:
        export_news(**kwargs)
    elif sender is Feedback:
        export_feedback(**kwargs) 
    elif sender is PendingSubscriptionNotification:
        export_pending_subscription_notifications(**kwargs)
    elif sender is Resource:
        export_resources(**kwargs)
    elif sender is InLitResource:
        export_inlitresources(**kwargs)
    elif sender is Submission:        
        export_submissions(**kwargs)
    elif sender is Subscription:        
        export_subscriptions(**kwargs)
    elif sender is TeamMember:
        export_team(**kwargs)
    elif sender is ToolType:
        export_tool_types(**kwargs)
