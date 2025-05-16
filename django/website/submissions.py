from datetime import timezone
import json, uuid

from django.conf import settings
from django.core.mail import send_mail
from django.http import Http404, HttpRequest, HttpResponse
from django.forms import CheckboxSelectMultiple, ModelForm, ValidationError
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Button, Submit
from ipware import get_client_ip

from .constants import SaveType
from .models import Resource, Submission, SubmissionStatus
from .utils import organized_categories_json

from hssi import settings

class SubmissionForm(ModelForm):
    class Meta:
        model = Submission
        fields = [
            'submitter_contact', 
            'name', 
            'logo_url', 
            'logo', 
            'author', 
            'release_url',
            'repo_url',
            'docs_url', 
            'website_url', 
            'description',
            'version', 
            'code_language', 
            'search_keywords', 
            'related_tools', 
            'submission_notes',
            'categories',
            'collections',
            'tool_types',
            'other_category',
        ]
        help_texts = Submission.help_texts
        labels = Submission.labels
        widgets = {
            'categories': CheckboxSelectMultiple()
        }

    def clean_id(self):
 
        submission_id = self.cleaned_data['id']

        if submission_id is None: # If this is a new Submission, not an edit ...
            submission_id = uuid.uuid4()
 
        return submission_id

    def clean_name(self):
 
        resource_name = self.cleaned_data['name']

        if self.instance is None or self.instance.id is None: # If this is a new Submission, not an edit ...
            if Resource.objects.filter(name=resource_name).exists() or Submission.objects.filter(name=resource_name).exists():
                raise ValidationError(_("A resource name must be unique, please enter a different name"))
 
        return resource_name

    def __init__(self, *args, **kwargs):
        super(SubmissionForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.fields['submitter_contact'].required = True
        self.helper.form_class = 'form'
        self.helper.form_id = 'id-submission_form'
        self.helper.form_method = 'POST'

def email_strings_for(submission: Submission, save_type: SaveType, changed_fields: dict | None):

    domain = settings.SITE_DOMAIN
    protocol = settings.SITE_PROTOCOL

    # If this is a brand new submission, create an email for admin and the submitter that outline all of the fields
    if save_type is SaveType.SUBMIT:
        submission_text = submission.detail_string()
        subject = "A new resource was submitted"

        admin_message = str(f"A web user has submitted a new resource via {protocol}://{domain}/submissions/\n\n")
        admin_message += submission_text
        admin_message += str(f"\n\nTo review and manage this submission, go to {protocol}://{domain}/admin/website/submission/")
    
        submitter_message = "Thank you for submitting a new resource! All new resources are reviewed for readiness and alignment with our strategic goals before they are posted and/or prepared for further development. The team will review your submission and contact you for further information if needed.\n\n"
        submitter_message += submission_text
        submitter_message += str(f"\n\nIf you would like to review or revise your submission you may do so here: {protocol}://{domain}/submissions/{submission.id}/")
    # This section is for when a submission that already exists is edited and highlights what has changed compared to its
    # previous version.
    elif save_type is SaveType.EDIT:
        subject = "A submission was edited"
        
        # Create the message sent specifically to admins that highlights which fields changed
        admin_submission_text = ""
       
        if "name" in changed_fields:
            if changed_fields["name"][0] != "":
                admin_submission_text += "OLD name: " + changed_fields["name"][0] + "\n"
            
            admin_submission_text += "NEW name: " + changed_fields["name"][1] + "\n\n"
        else:
            admin_submission_text += "name: " + submission.name + "\n\n"

        if "submitter_contact" in changed_fields:
            if changed_fields["submitter_contact"][0] != "":
                admin_submission_text += "OLD submitter_contact: " + changed_fields["submitter_contact"][0] + "\n"
            admin_submission_text += "NEW submitter_contact: " + changed_fields["submitter_contact"][1] + "\n\n"
        else:
            admin_submission_text += "submitter_contact: " + submission.submitter_contact + "\n\n"

        admin_submission_text += "categories: "
        for category in submission.categories.all():
            admin_submission_text += category.name + ", "
        
        admin_submission_text += "\n\n"

        admin_submission_text += "ALTERED FIELDS = " + ", ".join(changed_fields.keys()) + "\n\n"

        for field in changed_fields:
            if field == "name" or field == "submitter_contact":
                pass
            else:
                if changed_fields[field][0] != "":
                    admin_submission_text += "OLD " + field + ": " + str(changed_fields[field][0]) + "\n\n"
                admin_submission_text += "NEW " + field + ": " + str(changed_fields[field][1]) + "\n\n"

        # This creates an email string to send to the submitter that siply outlines all of the fields
        submission_text = submission.detail_string()

        admin_message = str(f"A web user has revised a submission via {protocol}://{domain}/submissions/{submission.id}/\n\n")

        admin_message += admin_submission_text
        admin_message += str(f"\n\nTo review and manage this submission, go to {protocol}://{domain}/admin/website/submission/")

        submitter_message = "Thank you for revising your submission! All revised submissions are reviewed for readiness and alignment with our strategic goals before they are posted and/or prepared for further development. The team will review your submission and contact you for further information if needed.\n\n"
        submitter_message += submission_text
        submitter_message += str(f"\n\nIf you would like to further review or revise your submission you may do so here: {protocol}://{domain}/submissions/{submission.id}")
    
    elif save_type is SaveType.FIRSTCONTACT:
        subject = "Listing a resource on HSSI"
        
        context = {'tool_name': submission.name,
                   'tool_id': submission.id,
                   "tool_contact_order": submission.contact_count,
                   "tool_is_inlit_elig": False,
                   "site_protocol": settings.SITE_PROTOCOL,
                   "site_domain": settings.SITE_DOMAIN}
        
        submitter_message = render_to_string('website/contact_email_conditionals.html', context)
        
        admin_message = str(f"First Contact Email(s) Sent (See Below)\n\n")
        admin_message += str(f"\"{submitter_message}\"")
        admin_message += str(f"\n\nTo review and manage the submissions, go to https://{domain}/admin/website/submission/")
        
    elif save_type is SaveType.RECONTACT:
        subject = "Listing a resource on HSSI"
        
        context = {'tool_name': submission.name,
                   'tool_id': submission.id,
                   "tool_contact_order": submission.contact_count,
                   "tool_is_inlit_elig": False,
                   "site_protocol": settings.SITE_PROTOCOL,
                   "site_domain": settings.SITE_DOMAIN}
        
        submitter_message = render_to_string('website/contact_email_conditionals.html', context)
        
        admin_message = str(f"Recontact Email(s) Sent (See Below)\n\n")
        admin_message += str(f"\"{submitter_message}\"")
        admin_message += str(f"\n\nTo review and manage the submissions, go to https://{domain}/admin/website/submission/")
        
    elif save_type is SaveType.FINALCONTACT:
        subject = "Listing a resource on HSSI"
        
        context = {'tool_name': submission.name,
                   'tool_id': submission.id,
                   "tool_contact_order": submission.contact_count,
                   "tool_is_inlit_elig": False,
                   "site_protocol": settings.SITE_PROTOCOL,
                   "site_domain": settings.SITE_DOMAIN}
        
        submitter_message = render_to_string('website/contact_email_conditionals.html', context)
        
        admin_message = str(f"Final Contact Email(s) Sent (See Below)\n\n")
        admin_message += str(f"\"{submitter_message}\"")
        admin_message += str(f"\n\nTo review and manage the submissions, go to https://{domain}/admin/website/submission/")

    elif save_type is SaveType.INITIALINLITCONTACT:
        subject = "Listing a resource on HSSI"
        
        context = {'tool_name': submission.name,
                   'tool_id': submission.id,
                   "tool_contact_order": submission.contact_count,
                   "tool_is_inlit_elig": True,
                   "site_protocol": settings.SITE_PROTOCOL,
                   "site_domain": settings.SITE_DOMAIN}
        
        submitter_message = render_to_string('website/contact_email_conditionals.html', context)
        
        admin_message = str(f"Initial In-Lit Email(s) Sent (See Below)\n\n")
        admin_message += str(f"\"{submitter_message}\"")
        admin_message += str(f"\n\nTo review and manage the submissions, go to https://{domain}/admin/website/submission/")

    elif save_type is SaveType.SECONDINLITCONTACT:
        subject = "Listing a resource on HSSI"
        
        context = {'tool_name': submission.name,
                   'tool_id': submission.id,
                   "tool_contact_order": submission.contact_count,
                   "tool_is_inlit_elig": True,
                   "site_protocol": settings.SITE_PROTOCOL,
                   "site_domain": settings.SITE_DOMAIN}
        
        submitter_message = render_to_string('website/contact_email_conditionals.html', context)
        
        admin_message = str(f"Second In-Lit Email(s) Sent (See Below)\n\n")
        admin_message += str(f"\"{submitter_message}\"")
        admin_message += str(f"\n\nTo review and manage the submissions, go to https://{domain}/admin/website/submission/")
    
    elif save_type is SaveType.FINALINLITCONTACT:
        subject = "Listing a resource on HSSI"
        
        context = {'tool_name': submission.name,
                   'tool_id': submission.id,
                   "tool_contact_order": submission.contact_count,
                   "tool_is_inlit_elig": True,
                   "site_protocol": settings.SITE_PROTOCOL,
                   "site_domain": settings.SITE_DOMAIN}
        
        submitter_message = render_to_string('website/contact_email_conditionals.html', context)
        
        admin_message = str(f"Final In-Lit Email(s) Sent (See Below)\n\n")
        admin_message += str(f"\"{submitter_message}\"")
        admin_message += str(f"\n\nTo review and manage the submissions, go to https://{domain}/admin/website/submission/")
 
    return subject, admin_message, submitter_message

def is_valid_email(value: str) -> bool:
    is_valid = True
    try:
        validate_email(value)
    except ValidationError:
        is_valid = False
    else:
        is_valid = True
    
    return is_valid

def submission_was_saved(submission: Submission, save_type: SaveType, changed_fields: dict | None = None):

    from_address = settings.ADMIN_EMAIL
    admin_to_address = settings.ADMIN_EMAIL

    subject, admin_message, submitter_message = email_strings_for(submission, save_type, changed_fields)

    submitter_contact = str(submission.submitter_contact)
    submitter_contact_is_email = is_valid_email(submitter_contact)
    
    # Send emails to submitter, admins
    if settings.SITE_DOMAIN.startswith("your-prod-server"):

        if submitter_contact_is_email:
            # Any of the Contact Emails have html templates, so we need to use the html_message paramter
            if save_type is SaveType.FIRSTCONTACT or save_type is SaveType.RECONTACT or save_type is SaveType.FINALCONTACT or save_type is SaveType.INITIALINLITCONTACT or save_type is SaveType.SECONDINLITCONTACT or save_type is SaveType.FINALINLITCONTACT:
                send_mail(subject, submitter_message, from_address, [submitter_contact], fail_silently=False, html_message=submitter_message)
            else:
                # is new or edit, send plain email
                send_mail(subject, submitter_message, from_address, [submitter_contact], fail_silently=False)

        # send the admin email if the submitter was emailed OR if it is a new or edited submission
        # but not if it was a failed contact email (faled due to contact info not being a valid email)
        if (submitter_contact_is_email or save_type is SaveType.SUBMIT or save_type is SaveType.EDIT):
            send_mail(subject, admin_message, from_address, [admin_to_address], fail_silently=False,)

    else:
        if settings.SITE_DOMAIN.startswith("your-dev-server"):
            # send admin emails only for testing
            if save_type is SaveType.FIRSTCONTACT or save_type is SaveType.RECONTACT or save_type is SaveType.FINALCONTACT or save_type is SaveType.INITIALINLITCONTACT or save_type is SaveType.SECONDINLITCONTACT or save_type is SaveType.FINALINLITCONTACT:
                send_mail(subject, None, from_address, [admin_to_address], fail_silently=False, html_message=admin_message)  
            else:
                send_mail(subject, admin_message, from_address, [admin_to_address], fail_silently=False)
        # # send email to console in local dev
        # # (requires uncommenting setting in settings.py)
        # elif settings.SITE_DOMAIN == "lvh.me":
        #     send_mail(subject, admin_message, from_address, [admin_to_address], fail_silently=False)

def rectify_categories_for(submission: Submission):
    categories = submission.categories.all()
    for category in categories:
        if category.has_parents():
            for parent in category.parents.all():
                if not parent in categories:
                    submission.categories.add(parent)

def submit(request: HttpRequest) -> HttpResponse:

    if request.POST:
        submission_form = SubmissionForm(request.POST, request.FILES)

        if submission_form.is_valid():

            client_ip, is_routable = get_client_ip(request)
            if client_ip is not None and is_routable:
                submission_form.submitter_ip_address = client_ip

            submission = submission_form.save()
            submission.status = SubmissionStatus.RECEIVED
            submission.last_curated_date = timezone.now()

            rectify_categories_for(submission)

            submission.save()
            submission_was_saved(submission, SaveType.SUBMIT)

            request.session['submission_id'] = str(submission.id)
            
            return redirect('/submissions/success/')

    else:
        submission_form = SubmissionForm()


    submission_form.helper.form_action = '/submissions/'
    submission_form.helper.add_input(Submit('newSubmit', 'Submit', css_class='hollow button'))

    category_hierarchy_json, category_names_by_id_json = organized_categories_json()

    context = {
        'category_hierarchy_json': category_hierarchy_json,
        'category_names_by_id_json': category_names_by_id_json,
        'form': submission_form
    }

    return render(request, 'website/submission.html', context)

def success(request: HttpRequest) -> HttpResponse:

    submission_id = uuid.UUID(request.session.get('submission_id'))
    submission = Submission.objects.get(id=submission_id)

    category_list = ', '.join([category.name for category in submission.categories.all()])
    collection_list = ', '.join([collection.name for collection in submission.collections.all()])
    tooltype_list = ', '.join([tool_type.name for tool_type in submission.tool_types.all()])

    context = {
        'submission': submission,
        'category_list': category_list,
        'collection_list': collection_list,
        'tooltype_list': tooltype_list,
        'id': submission_id
    }

    return render(request, 'website/submission_success.html', context)

def edit(request: HttpRequest, id: str) -> HttpResponse:

    submission_form = None
    selected_category_ids = []

    if request.POST:
        submission_form = SubmissionForm(request.POST, request.FILES, instance=Submission.objects.get(id=id))

        if submission_form.is_valid():

            client_ip, is_routable = get_client_ip(request)
            if client_ip is not None and is_routable:
                submission_form.submitter_ip_address = client_ip

            cls = Submission
            old_submission = cls.objects.get(pk=id)
            
            submission = submission_form.save()
            
            clsNew = submission.__class__
            # This will get the current model state since super().save() isn't called yet.
            new_submission = submission  # This gets the newly instantiated Model object with the new values.
            old_fields = {}
            new_fields = {}
            changed_fields = {}
            for field in clsNew._meta.get_fields():
                field_name = field.name
                try:
                    if getattr(old_submission, field_name) != getattr(new_submission, field_name):
                        old_fields[field_name] = getattr(old_submission, field_name)
                        new_fields[field_name] = getattr(new_submission, field_name)
                        changed_fields[field_name] = [old_fields[field_name], new_fields[field_name]]
                except Exception as ex:  # Catch field does not exist exception
                    pass

            submission.creation_date = timezone.now()
            submission.last_curated_date = timezone.now()
            submission.has_unsynced_changes = True if hasattr(submission, 'resource') else False
            rectify_categories_for(submission)
            if submission.status in [SubmissionStatus.CONTACTED, SubmissionStatus.IN_LITERATURE, SubmissionStatus.REJECTED_ABANDONED]:
                submission.status = SubmissionStatus.RECEIVED
            
            submission.save()

            save_type = SaveType.EDIT
            submission_was_saved(submission, save_type, changed_fields)

            request.session['submission_id'] = str(submission.id)

            return redirect('/submissions/success/')
    else:
        try:
            submission_id = uuid.UUID(id)
            submission = Submission.objects.get(id=submission_id)

            if submission:
                for category in submission.categories.all():
                    selected_category_ids.append(str(category.id))

                submission_form = SubmissionForm(instance=submission)
                submission_form.helper.form_action = str(f'/submissions/{submission_id}/')
                submission_form.helper.add_input(Submit('save', 'Save', css_class='hollow button save'))
                submission_form.helper.add_input(Button('cancel', 'Cancel', css_class='hollow button cancel', onclick=f"window.location.href='/';"))

        except: 
            raise Http404("Submission does not exist")

    category_hierarchy_json, category_names_by_id_json = organized_categories_json()
    
    context = {
        'category_hierarchy_json': category_hierarchy_json,
        'category_names_by_id_json': category_names_by_id_json,
        'selected_category_ids_json': json.dumps(selected_category_ids),
        'submission_form': submission_form
    }

    return render(request, 'website/submission.html', context)

def send_contact_email(submission: Submission, save_type: SaveType):
    submission_was_saved(submission, save_type)
