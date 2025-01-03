from datetime import timezone
import json, uuid

from django.conf import settings
from django.core.mail import send_mail
from django.http import Http404
from django.forms import CheckboxSelectMultiple, ModelForm, ValidationError
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Button, Submit
from ipware import get_client_ip

import requests

from .constants import SaveType
from .models import Resource, Submission, SubmissionStatus
from .utils import organized_categories_json

from emac import settings

class SubmissionForm(ModelForm):

    class Meta:
        model = Submission
        fields = [
            'submitter_first_name', 'submitter_last_name', 'submitter_email', 
            'name', 'credits', 'description', 'subtitle', 'version', 
            'search_keywords', 'code_languages', 'logo_image', 'logo_link', 
            'related_tool_string', 'host_app_on_emac', 'host_data_on_emac', 
            'private_code_or_data_link', 'submission_notes','categories',
            'other_category', 'about_link', 'ads_abstract_link', 
            'download_link', 'download_data_link','jupyter_link', 
            'launch_link', 'demo_link','ascl_id',
            #'captcha'
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

        # If this is a new Submission, not an edit ...
        if self.instance is None or self.instance.id is None: 
            if (
                Resource.objects.filter(name=resource_name).exists() or 
                Submission.objects.filter(name=resource_name).exists()
                ):
                raise ValidationError(_(
                    "An EMAC resource name must be unique, " +
                    "please enter a different name"
                ))
 
        return resource_name

    def clean_submitter_email(self):
        submitter_email = self.cleaned_data['submitter_email']

        return submitter_email

    def __init__(self, *args, **kwargs):
        super(SubmissionForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.fields['submitter_first_name'].required = True
        self.helper.form_class = 'form'
        self.helper.form_id = 'id-submission_form'
        self.helper.form_method = 'POST'
        

def email_strings_for(submission, save_type, changed_fields, curator):

    domain = settings.EMAC_DOMAIN

    # If this is a brand new submission, create an email for admin and the 
    # submitter that outline all of the fields
    if save_type is SaveType.SUBMIT:
        submission_text = submission.detail_string()
        subject = "EMAC: A new resource was submitted"

        admin_message = str(
            "A web user has submitted a new resource to EMAC via " +
            f"https://{domain}/submissions/\n\n"
        )
        admin_message += submission_text
        admin_message += str(
            f"\n\nTo review and manage this submission, go to " +
            f"https://{domain}/admin/website/submission/"
        )
    
        submitter_message = (
            "Thank you for submitting a new resource to the Exoplanet " +
            "Modeling & Analysis Center! All new resources are reviewed " +
            "for readiness and alignment with the EMAC strategic goals " +
            "before they are posted and/or prepared for further " +
            "development. The EMAC team will review your submission and " +
            "contact you for further information if needed.\n\n"
        )
        submitter_message += submission_text
        submitter_message += str(
            "\n\nIf you would like to review or revise your submission "+
            f"you may do so here: https://{domain}/submissions/{submission.id}/"
        )
    # This section is for when a submission that already exists is edited and 
    # highlights what has changed compared to its previous version.
    elif save_type is SaveType.EDIT or save_type is SaveType.CURATE:
        subject = "EMAC: A submission was edited"
        
        # Create the message sent specifically to admins that highlights which 
        # fields changed
        admin_submission_text = ""
       
        if "name" in changed_fields:
            if changed_fields["name"][0] != "":
                admin_submission_text += "OLD name: " + changed_fields["name"][0] + "\n"
            admin_submission_text += "NEW name: " + changed_fields["name"][1] + "\n\n"

        else:
            admin_submission_text += "name: " + submission.name + "\n\n"
        
        if "submitter_first_name" in changed_fields:
            if changed_fields["submitter_first_name"][0] != "":
                admin_submission_text += (
                    "OLD submitter_first_name: " + 
                    changed_fields["submitter_first_name"][0] + "\n"
                )
            admin_submission_text += (
                "NEW submitter_first_name: " + 
                changed_fields["submitter_first_name"][1] + "\n\n"
            )

        else:
            admin_submission_text += (
                "submitter_first_name: " + 
                submission.submitter_first_name + "\n\n"
            )

        if "submitter_last_name" in changed_fields:
            if changed_fields["submitter_last_name"][0] != "":
                admin_submission_text += (
                    "OLD submitter_last_name: " + 
                    changed_fields["submitter_last_name"][0] + "\n"
                )
            admin_submission_text += (
                "NEW submitter_last_name: " + 
                changed_fields["submitter_last_name"][1] + "\n\n"
            )
        
        else:
            admin_submission_text += (
                "submitter_last_name: " + 
                submission.submitter_last_name + "\n\n"
            )

        if "submitter_email" in changed_fields:
            if changed_fields["submitter_email"][0] != "":
                admin_submission_text += (
                    "OLD submitter_email: " + 
                    changed_fields["submitter_email"][0] + "\n"
                )
            admin_submission_text += (
                "NEW submitter_email: " + 
                changed_fields["submitter_email"][1] + "\n\n"
            )
        else:
            admin_submission_text += "submitter_email: " + submission.submitter_email + "\n\n"

        admin_submission_text += "categories: "
        for category in submission.categories.all():
            admin_submission_text += category.name + ", "
        admin_submission_text += "\n\n"
        admin_submission_text += "ALTERED FIELDS = " + ", ".join(changed_fields.keys()) + "\n\n"

        for field in changed_fields:
            
            if not (
                field == "name" or 
                field == "submitter_first_name" or 
                field == "submitter_last_name" or 
                field == "submitter_email"
            ):
                if changed_fields[field][0] != "":
                    admin_submission_text += (
                        "OLD " + field + ": " + 
                        str(changed_fields[field][0]) + "\n\n"
                    )
                admin_submission_text += (
                    "NEW " + field + ": " + 
                    str(changed_fields[field][1]) + "\n\n"
                )

        # This creates an email string to send to the submitter that simply 
        # outlines all of the fields
        submission_text = submission.detail_string()

        if save_type is SaveType.EDIT:
            admin_message = str(
                "A web user has revised a submission via " +
                f"https://{domain}/submissions/{submission.id}/\n\n"
            )
        elif save_type is SaveType.CURATE:
            admin_message = str(f"A web user has revised a submission via the curators form.\n\n")
            if curator and curator.is_authenticated:
                admin_message += "Curator: " + curator.username + "\n\n"
            else:
                admin_message += "(Curator unknown)\n\n"

        admin_message += admin_submission_text
        admin_message += str(
            "\n\nTo review and manage this submission, go to " +
            f"https://{domain}/admin/website/submission/"
        )

        submitter_message = (
            "Thank you for revising your submission to the Exoplanet " +
            "Modeling & Analysis Center! All revised submissions are " +
            "reviewed for readiness and alignment with the EMAC strategic " +
            "goals before they are posted and/or prepared for further " +
            "development. The EMAC team will review your submission and " +
            "contact you for further information if needed.\n\n"
        )
        submitter_message += submission_text
        submitter_message += str(
            "\n\nIf you would like to further review or revise your " +
            "submission you may do so here: " +
            f"https://{domain}/submissions/{submission.id}")
    
    elif save_type is SaveType.FIRSTCONTACT:
        
        subject = "Listing Software on the NASA Exoplanet Modeling & Analysis Center"
        context = {
            "submitter_first_name": submission.submitter_first_name,
            "tool_name": submission.name,
            "tool_id": submission.id,
            "tool_contact_order": submission.contact_count,
            "tool_is_inlit_elig": False
        }
        submitter_message = render_to_string(
            'website/contact_email_conditionals.html', 
            context
        )
        
        admin_message = str(f"First Contact Email(s) Sent (See Below)\n\n")
        admin_message += str(f"\"{submitter_message}\"")
        admin_message += str(
            "\n\nTo review and manage the submissions, go to " +
            f"https://{domain}/admin/website/submission/"
        )
        
    elif save_type is SaveType.RECONTACT:

        subject = "Listing Software on the NASA Exoplanet Modeling & Analysis Center"
        context = {
            "submitter_first_name": submission.submitter_first_name,
            "tool_name": submission.name,
            "tool_id": submission.id,
            "tool_contact_order": submission.contact_count,
            "tool_is_inlit_elig": False
        }
        submitter_message = render_to_string(
            "website/contact_email_conditionals.html", 
            context
        )
        
        admin_message = str(f"Recontact Email(s) Sent (See Below)\n\n")
        admin_message += str(f"\"{submitter_message}\"")
        admin_message += str(
            "\n\nTo review and manage the submissions, go to " +
            f"https://{domain}/admin/website/submission/"
        )
        
    elif save_type is SaveType.FINALCONTACT:
        
        subject = "Listing Software on the NASA Exoplanet Modeling & Analysis Center"
        context = {
            "submitter_first_name": submission.submitter_first_name,
            "tool_name": submission.name,
            "tool_id": submission.id,
            "tool_contact_order": submission.contact_count,
            "tool_is_inlit_elig": False
        }
        submitter_message = render_to_string(
            "website/contact_email_conditionals.html", 
            context
        )
        
        admin_message = str(f"Final Contact Email(s) Sent (See Below)\n\n")
        admin_message += str(f"\"{submitter_message}\"")
        admin_message += str(
            "\n\nTo review and manage the submissions, go to " +
            f"https://{domain}/admin/website/submission/"
        )

    elif save_type is SaveType.INITIALINLITCONTACT:
        
        subject = "Listing Software on the NASA Exoplanet Modeling & Analysis Center"
        context = {
            "submitter_first_name": submission.submitter_first_name,
            "tool_name": submission.name,
            "tool_id": submission.id,
            "tool_contact_order": submission.contact_count,
            "tool_is_inlit_elig": True
        }
        submitter_message = render_to_string('website/contact_email_conditionals.html', context)
        
        admin_message = str(f"Initial In-Lit Email(s) Sent (See Below)\n\n")
        admin_message += str(f"\"{submitter_message}\"")
        admin_message += str(
            f"\n\nTo review and manage the submissions, go to " +
            f"https://{domain}/admin/website/submission/"
        )

    elif save_type is SaveType.SECONDINLITCONTACT:
        
        subject = "Listing Software on the NASA Exoplanet Modeling & Analysis Center"
        context = {
            "submitter_first_name": submission.submitter_first_name,
            "tool_name": submission.name,
            "tool_id": submission.id,
            "tool_contact_order": submission.contact_count,
            "tool_is_inlit_elig": True
        }
        submitter_message = render_to_string(
            "website/contact_email_conditionals.html", 
            context
        )
        
        admin_message = str(f"Second In-Lit Email(s) Sent (See Below)\n\n")
        admin_message += str(f"\"{submitter_message}\"")
        admin_message += str(
            "\n\nTo review and manage the submissions, go to " +
            f"https://{domain}/admin/website/submission/"
        )
    
    elif save_type is SaveType.FINALINLITCONTACT:
        
        subject = "Listing Software on the NASA Exoplanet Modeling & Analysis Center"
        context = {
            "submitter_first_name": submission.submitter_first_name,
            "tool_name": submission.name,
            "tool_id": submission.id,
            "tool_contact_order": submission.contact_count,
            "tool_is_inlit_elig": True
        }
        submitter_message = render_to_string('website/contact_email_conditionals.html', context)
        
        admin_message = str(f"Final In-Lit Email(s) Sent (See Below)\n\n")
        admin_message += str(f"\"{submitter_message}\"")
        admin_message += str(
            "\n\nTo review and manage the submissions, go to " +
            f"https://{domain}/admin/website/submission/"
        )
 
    return subject, admin_message, submitter_message

def submission_was_saved(submission, save_type, changed_fields=None, curator=None):

    from_address = "REDACTED@nasa.gov" # JPR Redacted Oct. 2024
    admin_to_address = "REDACTED@nasa.gov" # JPR Redacted Oct. 2024

    subject, admin_message, submitter_message = email_strings_for(submission, 
        save_type, 
        changed_fields, 
        curator
    )

    data = '{"text":"' + admin_message + '"}'
    headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
    
    # Send emails to submitter, EMAC admins, and a Slack notification
    if settings.EMAC_DOMAIN.startswith("emac.gsfc"):

        requests.post(
            settings.EMAC_SUBMISSION_SLACK_URL, 
            data=data.encode('utf-8'), 
            headers=headers
        )
        # Any of the Contact Emails have html templates, so we need to use 
        # the html_message paramter
        if (
            save_type is SaveType.FIRSTCONTACT or 
            save_type is SaveType.RECONTACT or 
            save_type is SaveType.FINALCONTACT or 
            save_type is SaveType.INITIALINLITCONTACT or 
            save_type is SaveType.SECONDINLITCONTACT or 
            save_type is SaveType.FINALINLITCONTACT
        ):
            send_mail(
                subject, 
                submitter_message, 
                from_address, 
                [str(submission.submitter_email)], 
                fail_silently=False, 
                html_message=submitter_message
            )

        # _only_ send an email to the original submitter if the save came
        # from the regular submission or edit form, not the curators form
        else:
            if save_type is not SaveType.CURATE:
                send_mail(
                    subject, 
                    submitter_message, 
                    from_address, 
                    [str(submission.submitter_email)], 
                    fail_silently=False
                )
            
            # always send the admin email
            send_mail(
                subject, 
                admin_message, 
                from_address, 
                [admin_to_address], 
                fail_silently=False
            )
    else:
        if settings.EMAC_DOMAIN.startswith("emac-dev"):
            if (
                save_type is SaveType.FIRSTCONTACT or 
                save_type is SaveType.RECONTACT or 
                save_type is SaveType.FINALCONTACT or 
                save_type is SaveType.INITIALINLITCONTACT or 
                save_type is SaveType.SECONDINLITCONTACT or 
                save_type is SaveType.FINALINLITCONTACT
            ):
                # send_mail(subject, None, from_address, [str(submission.submitter_email)], fail_silently=False, html_message=submitter_message)
                send_mail(
                    subject, 
                    None, 
                    from_address, 
                    [admin_to_address], 
                    fail_silently=False, 
                    html_message=admin_message
                )
            else:
                # send_mail(subject, submitter_message, from_address, [str(submission.submitter_email)], fail_silently=False)
                send_mail(
                    subject, 
                    admin_message, 
                    from_address, 
                    [admin_to_address], 
                    fail_silently=False
                )
    
        # # send email to console in local dev
        # # (requires uncommenting setting in /EMAC/django/emac/seetings.py)
        # elif settings.EMAC_DOMAIN == "lvh.me":
        #     send_mail(
        #         subject, 
        #         admin_message, 
        #         from_address, 
        #         [admin_to_address], 
        #         fail_silently=False
        #     )

        requests.post(
            settings.EMAC_SUBMISSION_TEST_SLACK_URL, 
            data=data.encode('utf-8'), 
            headers=headers
        )


def rectify_categories_for(submission):

    categories = submission.categories.all()    
    for category in categories:
        if category.has_parents():
            for parent in category.parents.all():
                if not parent in categories:
                    submission.categories.add(parent)
    
    submission.save()

def submit(request):

    if request.POST:
        submission_form = SubmissionForm(request.POST, request.FILES)

        if submission_form.is_valid():

            client_ip, is_routable = get_client_ip(request)
            if client_ip is not None and is_routable:
                submission_form.submitter_ip_address = client_ip

            submission = submission_form.save()
            submission.status = SubmissionStatus.RECEIVED.name
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
        'submission_form': submission_form
    }

    return render(request, 'website/submission.html', context)

def success(request):

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

def edit(request, id):

    submission_form = None
    selected_category_ids = []

    if request.POST:
        submission_form = SubmissionForm(
            request.POST, 
            request.FILES, 
            instance=Submission.objects.get(id=id)
        )

        if submission_form.is_valid():

            client_ip, is_routable = get_client_ip(request)
            if client_ip is not None and is_routable:
                submission_form.submitter_ip_address = client_ip

            cls = Submission
            old_submission = cls.objects.get(pk=id)
            
            submission = submission_form.save()
            
            # This will get the current model state since super().save() isn't called yet.
            clsNew = submission.__class__
            # This gets the newly instantiated Model object with the new values.
            new_submission = submission
            old_fields = {}
            new_fields = {}
            changed_fields = {}
            for field in clsNew._meta.get_fields():
                field_name = field.name
                try:
                    if getattr(old_submission, field_name) != getattr(new_submission, field_name):
                        old_fields[field_name] = getattr(old_submission, field_name)
                        new_fields[field_name] = getattr(new_submission, field_name)
                        changed_fields[field_name] = [
                            old_fields[field_name], 
                            new_fields[field_name]
                        ]
                except Exception as ex:  # Catch field does not exist exception
                    pass
            # kwargs['update_fields'] = changed_fields

            submission.last_modification_date = timezone.now()
            submission.last_curated_date = timezone.now()
            submission.has_unsynced_changes = True if hasattr(submission, 'resource') else False
            rectify_categories_for(submission)
            if (
                submission.status in [
                    SubmissionStatus.CONTACTED.name, 
                    SubmissionStatus.IN_LITERATURE.name, 
                    SubmissionStatus.REJECTED_ABANDONED.name
                ]
            ):
                submission.status = SubmissionStatus.RECEIVED.name
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
                submission_form.helper.add_input(Submit(
                    'save', 'Save', 
                    css_class='hollow button save'
                ))
                submission_form.helper.add_input(Button(
                    'cancel', 'Cancel', 
                    css_class='hollow button cancel', 
                    onclick="window.location.href='/';"
                ))

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

def send_contact_email(submission, save_type):
    submission_was_saved(submission, save_type)


class ResourceUpdateForm(ModelForm):

    class Meta:
        model = Submission
        fields = [
            'github_release'
        ]
        help_texts = {
        'github_release': "The update message that will accompany this new version."
        }


    def clean_id(self):
 
        submission_id = self.cleaned_data['id']

        if submission_id is None: # If this is a new Submission, not an edit ...
            submission_id = uuid.uuid4()
 
        return submission_id


    def __init__(self, *args, **kwargs):
        super(ResourceUpdateForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.fields['github_release'].required = True
        self.helper.form_class = 'form'
        self.helper.form_id = 'id-submission_form'
        self.helper.form_method = 'POST'


def resource_update_alert(request, id):

    submission_form = None
    selected_category_ids = []

    if request.POST:
        submission_form = ResourceUpdateForm(
            request.POST, 
            request.FILES, 
            instance=Submission.objects.get(id=id)
        )

        if submission_form.is_valid():

            client_ip, is_routable = get_client_ip(request)
            if client_ip is not None and is_routable:
                submission_form.submitter_ip_address = client_ip

            cls = Submission
            old_submission = cls.objects.get(pk=id)
            
            submission = submission_form.save()
            
            # This will get the current model state since super().save() isn't called yet.
            clsNew = submission.__class__
            # This gets the newly instantiated Model object with the new values.
            new_submission = submission  
            old_fields = {}
            new_fields = {}
            changed_fields = {}
            for field in clsNew._meta.get_fields():
                field_name = field.name
                try:
                    if getattr(old_submission, field_name) != getattr(new_submission, field_name):
                        old_fields[field_name] = getattr(old_submission, field_name)
                        new_fields[field_name] = getattr(new_submission, field_name)
                        changed_fields[field_name] = [
                            old_fields[field_name], 
                            new_fields[field_name]
                        ]
                except Exception as ex:  # Catch field does not exist exception
                    pass
            # kwargs['update_fields'] = changed_fields

            submission.last_modification_date = timezone.now()
            submission.last_curated_date = timezone.now()
            submission.save()

            request.session['submission_id'] = str(submission.id)

            return redirect(f'/git_updates/{submission.id}/')
    else:
        try:
            submission_id = uuid.UUID(id)
            submission = Submission.objects.get(id=submission_id)

            if submission:
                for category in submission.categories.all():
                    selected_category_ids.append(str(category.id))

                submission_form = ResourceUpdateForm(instance=submission)
                submission_form.helper.form_action = str(f'/github_release_edit/{submission_id}/')
                submission_form.helper.add_input(Submit(
                    'save', 'Save', 
                    css_class='hollow button save'
                ))
                submission_form.helper.add_input(Button(
                    'cancel', 'Cancel', 
                    css_class='hollow button cancel', 
                    onclick=f"window.location.href='/';")
                )

        except: 
            raise Http404("Submission does not exist")

    category_hierarchy_json, category_names_by_id_json = organized_categories_json()
    
    context = {
        'category_hierarchy_json': category_hierarchy_json,
        'category_names_by_id_json': category_names_by_id_json,
        'selected_category_ids_json': json.dumps(selected_category_ids),
        'submission_form': submission_form,
        'submission_name': Submission.objects.get(id=id).name,
    }

    return render(request, 'website/submission_github_update.html', context)