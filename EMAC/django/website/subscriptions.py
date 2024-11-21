from datetime import timedelta
import json, uuid

from django.conf import settings
from django.core.mail import send_mail
from django.http import Http404
from django.forms import CheckboxSelectMultiple, ModelForm, ValidationError
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Button, Submit
from ipware import get_client_ip

from emac import emac_utils

from .constants import SaveType
from .models import Category, NotificationFrequency, PendingSubscriptionNotification, Resource, Subscription
from .utils import organized_categories_json

from emac import settings

# from django_recaptcha.fields import ReCaptchaField
# from django_recaptcha.widgets import ReCaptchaV3

emac_public_key, emac_private_key = emac_utils.get_recaptcha_keys()

class SubscriptionForm(ModelForm):

    # captcha = ReCaptchaField(
    #     public_key=emac_public_key,
    #     private_key=emac_private_key,
    #     widget=ReCaptchaV3(
    #         attrs={
    #             'required_score':0.7
    #         },
    #         action='subscription'
    #     )
    # )

    class Meta:
        model = Subscription

        fields = [
            'subscriber_email', 'categories', 'notification_frequency', 
            # 'captcha'
        ]
        help_texts = Subscription.help_texts
        # labels = Subscription.labels
        widgets = {
            'categories': CheckboxSelectMultiple()
        }

    def clean_subscriber_email(self):
        subscriber_email = self.cleaned_data['subscriber_email']
        if not emac_utils.email_address_is_allowed(subscriber_email):
            raise ValidationError(_("Subscriptions are not allowed from this email address"))

        return subscriber_email

    def clean_id(self):

        subscription_id = self.cleaned_data['id']
        if subscription_id is None:  # If this is a new Subscription, not an edit ...
            subscription_id = uuid.uuid4()
        return subscription_id

    def __init__(self, *args, **kwargs):
        super(SubscriptionForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_class = 'form'
        self.helper.form_id = 'id-subscription_form'
        self.helper.form_method = 'POST'

def email_strings_for(subscription, save_type, changed_fields=None):
    domain = settings.EMAC_DOMAIN
    # If this is a brand new subscription, create an email for admin and the subscriber that outline all of the fields
    if save_type is SaveType.SUBMIT:
        # subscription_text = subscription.detail_string()
        cat_string, freq_string, email_string = subscription.detail_string()
        subject = "EMAC: A new subscription was submitted"

        admin_message = str(f"An EMAC web user has subscribed to one or more categories via https://{domain}/subscriptions/\n\n")
        admin_message += cat_string + " " + freq_string + " " + email_string
        admin_message += str(f"\n\nTo review and manage this subscription, go to https://{domain}/admin/website/subscription/")
    
        subscriber_intro_message = "Thank you for subscribing to one or more resource categories in the Exoplanet Modeling & Analysis Center! Below are the subscription options you chose.\n\n" # for acknowledge

        context = {
            'intro': subscriber_intro_message,
            'categories': cat_string,
            'notification_frequency': freq_string,
            'subscriber_email': email_string,
            'subscription_edit': f'https://{domain}/subscriptions/{subscription.id}',
            'EMAC_DOMAIN': settings.EMAC_DOMAIN,
            'EMAC_PROTOCOL': settings.EMAC_PROTOCOL
        }

        plain_subscriber_message = context["intro"] + " \n\n" + context["categories"] + " \n\n" + context["notification_frequency"] + " \n\n" + context["subscriber_email"] + " \n\n" + context["subscription_edit"]
        subscriber_message = render_to_string('website/subscription_acknowledgement_email.html', context) # for acknowledge

    # This section is for when a subscription that already exists is edited and highlights what has changed compared to its
    # previous version.
    elif save_type is SaveType.EDIT:
        subject = "EMAC: A subscription was edited"
        
        # Create the message sent specifically to admins that highlights which fields changed
        admin_subscription_text = ""
       
        if "subscriber_email" in changed_fields:
            if changed_fields["subscriber_email"][0] != "":
                admin_subscription_text += "OLD subscriber_email: " + changed_fields["subscriber_email"][0] + "\n"
            admin_subscription_text += "NEW subscriber_email: " + changed_fields["subscriber_email"][1] + "\n\n"
        else:
            admin_subscription_text += "subscriber_email: " + subscription.subscriber_email + "\n\n"

        admin_subscription_text += "categories: "
        count = 0
        for category in subscription.categories.all():
            admin_subscription_text += str(subscription.categories.all()[count]) + ", "
            count += 1
        admin_subscription_text += "\n\n"

        admin_subscription_text += "ALTERED FIELDS = " + str(changed_fields.keys()) + "\n\n"

        # This creates an email string to send to the subscriber that siply outlines all of the fields
        # subscription_text = subscription.detail_string()
        cat_string, freq_string, email_string = subscription.detail_string()

        admin_message = str(f"A web user has revised a subscription via https://{domain}/subscriptions/{subscription.id}/\n\n")
        admin_message += admin_subscription_text
        admin_message += str(f"\n\nTo review and manage this subscription, go to https://{domain}/admin/website/subscription/")

        subscriber_intro_message = "Thank you for revising your subscription to the Exoplanet Modeling & Analysis Center! Below are the subscription options you chose.\n\n"

        context = {
            'intro': subscriber_intro_message,
            'categories': cat_string,
            'notification_frequency': freq_string,
            'subscriber_email': email_string,
            'subscription_edit': f'https://{domain}/subscriptions/{subscription.id}',
            'EMAC_DOMAIN': settings.EMAC_DOMAIN,
            'EMAC_PROTOCOL': settings.EMAC_PROTOCOL
        }

        plain_subscriber_message = context["intro"] + " \n\n" + context["categories"] + " \n\n" + context["notification_frequency"] + " \n\n" + context["subscriber_email"] + " \n\n" + context["subscription_edit"]
        subscriber_message = render_to_string('website/subscription_acknowledgement_email.html', context)
        
    return subject, admin_message, subscriber_message, plain_subscriber_message


# If this is an alert to a subscriber that a new tool was published, this section of the code builds the email.
def email_strings_for_notification(pending_subscription_notification):
    
    subscription = pending_subscription_notification.subscription

    subject = "EMAC: New tools and/or updates have been published!"

    admin_message = str(f"An EMAC Subscription alert was sent.\n\n")
    
    subscriber_intro_message = "New tools and/or updates have been published to your subscribed categories on the Exoplanet Modeling & Analysis Center!\n\n"

    resources_by_category = get_resources_from_subscriptions(pending_subscription_notification)

    context = {
        'intro': subscriber_intro_message,
        'resources': resources_by_category,
        'subscription_edit': f'{settings.EMAC_PROTOCOL}://{settings.EMAC_DOMAIN}/subscriptions/{subscription.id}',
        'EMAC_PROTOCOL': settings.EMAC_PROTOCOL,
        'EMAC_DOMAIN': settings.EMAC_DOMAIN
    }

    plain_subscriber_message = context["intro"] + " \n\n" + context["resources"] + " \n\n" + context["subscription_edit"]
    subscriber_message = render_to_string('website/subscription_notification_email.html', context)

    return subject, admin_message, subscriber_message, plain_subscriber_message


def subscription_was_saved(subscription, save_type, changed_fields=None):
    from_address = "REDACTED" # JPR Redacted Oct. 2024
    admin_to_address = "REDACTED" # JPR Redacted Oct. 2024
    print("subscription was saved")
    subject, admin_message, subscriber_message, plain_subscriber_message = email_strings_for(subscription, save_type, changed_fields)

    # If not on local lvh.me, send email to subscriber
    if settings.EMAC_DOMAIN.startswith("emac"):
        send_mail(subject, plain_subscriber_message, from_address, [str(subscription.subscriber_email)], fail_silently=False, html_message=subscriber_message)
        # If on dev, send email to admin as well
        if settings.EMAC_DOMAIN.startswith("emac-dev"):
            send_mail(subject, admin_message, from_address, [admin_to_address], fail_silently=False)

def submit(request):
    if request.POST:
        subscription_form = SubscriptionForm(request.POST, request.FILES)
        if subscription_form.is_valid():
            client_ip, is_routable = get_client_ip(request)
            if client_ip is not None and is_routable:
                subscription_form.subscriber_ip_address = client_ip

            subscription = subscription_form.save()
            subscription.save()
            subscription_was_saved(subscription, SaveType.SUBMIT)

            request.session['subscription_id'] = str(subscription.id)

            return redirect('/subscriptions/success/')
    else:
        subscription_form = SubscriptionForm()


    subscription_form.helper.form_action = '/subscriptions/'
    subscription_form.helper.add_input(Submit('btnSubmit', 'Submit', css_class='hollow button'))

    category_hierarchy_json, category_names_by_id_json = organized_categories_json()

    context = {
        'category_hierarchy_json': category_hierarchy_json,
        'category_names_by_id_json': category_names_by_id_json,
        'subscription_form': subscription_form
    }

    return render(request, 'website/subscription.html', context)

def success(request):

    subscription_id = uuid.UUID(request.session.get('subscription_id'))
    subscription = Subscription.objects.get(id=subscription_id)

    context = {
        # 'subscription': subscription.html_detail_string(),
        'id': subscription_id
    }

    return render(request, 'website/subscription_success.html', context)

def edit(request, id):

    subscription_form = None
    selected_category_ids = []

    if request.POST:
        subscription_form = SubscriptionForm(request.POST, request.FILES, instance=Subscription.objects.get(id=id))

        if subscription_form.is_valid():

            client_ip, is_routable = get_client_ip(request)
            if client_ip is not None and is_routable:
                subscription_form.subscriber_ip_address = client_ip

            cls = Subscription
            old_subscription = cls.objects.get(pk=id)
            subscription = subscription_form.save()
            clsNew = subscription.__class__
            # This will get the current model state since super().save() isn't called yet.
            new_subscription = subscription  # This gets the newly instantiated Mode object with the new values.
            old_fields = {}
            new_fields = {}
            changed_fields = {}
            for field in clsNew._meta.get_fields():
                field_name = field.name
                try:
                    if getattr(old_subscription, field_name) != getattr(new_subscription, field_name):
                        old_fields[field_name] = getattr(old_subscription, field_name)
                        new_fields[field_name] = getattr(new_subscription, field_name)
                        changed_fields[field_name] = [old_fields[field_name], new_fields[field_name]]
                except Exception as ex:  # Catch field does not exist exception
                    pass

            subscription.save()

            save_type = SaveType.EDIT
            subscription_was_saved(subscription, save_type, changed_fields)

            request.session['subscription_id'] = str(subscription.id)

            return redirect('/subscriptions/success/')
    else:
        try:
            subscription_id = uuid.UUID(id)
            subscription = Subscription.objects.get(id=subscription_id)

            if subscription:
                for category in subscription.categories.all():
                    selected_category_ids.append(str(category.id))

                subscription_form = SubscriptionForm(instance=subscription)
                subscription_form.helper.form_action = str(f'/subscriptions/{subscription_id}/')
                subscription_form.helper.add_input(Submit('save', 'Save', css_class='hollow button save'))
                subscription_form.helper.add_input(Button('cancel', 'Cancel', css_class='hollow button cancel', onclick="window.location.href='/';"))

        except: 
            raise Http404("Subscription does not exist")

    category_hierarchy_json, category_names_by_id_json = organized_categories_json()
    
    context = {
        'category_hierarchy_json': category_hierarchy_json,
        'category_names_by_id_json': category_names_by_id_json,
        'selected_category_ids_json': json.dumps(selected_category_ids),
        'subscription_form': subscription_form
    }

    return render(request, 'website/subscription.html', context)

def notify_subscribers(request, frequency=NotificationFrequency.DAILY.value):

    subscriptions = Subscription.objects.none()

    if frequency.lower() == NotificationFrequency.DAILY.value.lower():
        subscriptions_daily = Subscription.objects.filter(notification_frequency=NotificationFrequency.DAILY.name)
        subscriptions_immediately = Subscription.objects.filter(notification_frequency=NotificationFrequency.IMMEDIATELY.name)
        subscriptions = subscriptions_daily | subscriptions_immediately
    elif frequency.lower() == NotificationFrequency.WEEKLY.value.lower():
        subscriptions = Subscription.objects.filter(notification_frequency=NotificationFrequency.WEEKLY.name)

    if subscriptions:
        for pending_subscription_notification in PendingSubscriptionNotification.objects.filter(subscription__in=subscriptions):
            if pending_subscription_notification.is_due():
                send_notification_email(pending_subscription_notification)
                
                # Update the last notification date of the associated subscriptions
                subscription = Subscription.objects.get(id=pending_subscription_notification.subscription.id)
                subscription.last_notification_date = timezone.now()
                subscription.save()
                
                pending_subscription_notification.delete()
    
    return redirect('/')

def send_notification_email(pending_subscription_notification):

    from_address = "REDACTED" # JPR Redacted Oct. 2024
    admin_to_address = "REDACTED" # JPR Redacted Oct. 2024
    
    subject, admin_message, subscriber_message, plain_subscriber_message = email_strings_for_notification(pending_subscription_notification)

    subscription = pending_subscription_notification.subscription
    subscriber_email = subscription.subscriber_email
    is_internal = subscription.internal

    # default to not send emails, so no mail attempt
    # is made on lvh.me or localhost
    should_send_notification = False
    should_send_admin = False

    # if on emac-dev, only send emails if subscriber is internal
    # (i.e. part of the team) so regular subscribers do not get tesing emails
    if settings.EMAC_DOMAIN.startswith("emac-dev") and is_internal:
        should_send_notification = True
        should_send_admin = True  
    elif settings.EMAC_DOMAIN.startswith("emac.gsfc"):
        # if we are on prod, send regardless of "internal" status
        should_send_notification = True

    if (should_send_notification):
        # print("send_notification_email: sending subscriber email")
        send_mail(subject, plain_subscriber_message, from_address, [subscriber_email], fail_silently=False, html_message=subscriber_message)
    # else:
    #     print("send_notification_email: NOT sending subscriber email")

    if (should_send_admin):
        # print("send_notification_email: sending admin email")
        send_mail(f"{subject} (DEV)", admin_message, from_address, [admin_to_address], fail_silently=False)
    # else:
    #     print("send_notification_email: NOT sending admin email")


def resource_added_categories(resource, category_ids=None):

    print(f"resource: {resource} added category_ids: {category_ids}")

    # Retrieves the categories of the newly published tool
    if not category_ids:
        category_ids = resource.categories.all().values_list("id", flat=True)
    
    # Obtain the subscriptions that contain at least one of the newly published resource's categories
    subscriptions = Subscription.objects.filter(categories__id__in=category_ids).distinct()
    # 'subscriptions' is a queryset of subscriptions
        
    # Check for pending subscriptions that are linked to the QuerySet of subscriptions that subscribe to
    # the categories in the newly published resource
    existing_pending_subscriptions = PendingSubscriptionNotification.objects.filter(subscription__in=subscriptions).values('subscription')

    # Obtain a QuerySet of the subscriptions that do not already have a pending_sub_notif by excluding the previously created queryset
    new_pending_subscriptions = subscriptions.exclude(id__in=existing_pending_subscriptions)

    # Loop through the filtred subscriptions who already have a pending_sub_notif
    # Add this newly published resource to its resources many_to_many field
    for subscription in existing_pending_subscriptions:
        # Retrieve the pending_sub_notf object for the subscription currently being viewed
        current_pending_subscription_notification = PendingSubscriptionNotification.objects.filter(subscription=subscription['subscription'])#.values('resources')
        
        # Retrieve the resources that are already linked to the pending_subscription_notification
        current_pending_subscription_notification_resources = current_pending_subscription_notification.filter().values('resources')
        
        # If the resource is not already in the dictionary of resources associated with the
        # current_pending_subscription_notification, add it tot he resources field.
        if resource.id not in current_pending_subscription_notification_resources[0].values():
            current_pending_subscription_notification[0].resources.add(resource)
        
    # If there is no pending subscription yet, create a new pending subscription notification
    for subscription in new_pending_subscriptions:
        new_pending_subscription_notification = PendingSubscriptionNotification()
        
        # Assign the current subscription to this new pending_sub_notif
        new_pending_subscription_notification.subscription=subscription

        # Save the new pending_sub_notif; necessary before adding to the 'resources' many_to_many field
        new_pending_subscription_notification.save()
        new_pending_subscription_notification.resources.add(resource)
        new_pending_subscription_notification.save()
        
        # if new_pending_subscription_notification.is_due():
        if subscription.notification_frequency==NotificationFrequency.IMMEDIATELY.name:
            print("IMMEDIATE EMAIL SENT")

            send_notification_email(new_pending_subscription_notification)
            
            temp_id = new_pending_subscription_notification.subscription.id
            subscription = Subscription.objects.get(id=temp_id)
            subscription.last_notification_date = timezone.now()
            subscription.save()
            
            new_pending_subscription_notification.delete()

def get_categories(email):
    return Category.objects.filter(subscriptions__subscriber_email=email)

def get_resources(pendingsubscriptionnotification):
    return Resource.objects.filter(pendingsubscriptionnotification__id=id)
 
def get_resources_newer_than(days, tools):
    today = timezone.now()
    week_ago = timedelta(days=days)
    cutoff_date = today-week_ago
    return tools.filter(creation_date__gte=cutoff_date)
    
def get_resources_from_subscriptions(pending_subscription_notification):
    """takes subscription object as input, returns all resources associated
    with subscribers preferred categories"""

    resource_str = ""

    for resource in pending_subscription_notification.resources.all():
        cid = resource.citation_id
        name = resource.name
        subtitle = resource.subtitle
        credits = resource.credits
        concise_desc = resource.concise_description
        categories = resource.categories.all().values_list('name', flat=True)
        version_num = resource.version
        github_release_note = resource.submission.github_release

        separator = ", "

        # Add the New! and Updated! resource tags to differentiate between them
        # conditionally add the update notes if the associated submission has them
        if github_release_note:
            resource_str += f"<a class='upd-flag'>Updated!</a><a href='{settings.EMAC_PROTOCOL}://{settings.EMAC_DOMAIN}/?cid={cid}'><b>{name}:</b></a> {subtitle} <ul><li><b>Credits:</b> {credits}</li>"
            resource_str += f"<li><b>Release {version_num}:</b> {github_release_note}</li>"
        else:
            resource_str += f"<a class='new-flag'>New!</a><a href='{settings.EMAC_PROTOCOL}://{settings.EMAC_DOMAIN}/?cid={cid}'><b>{name}:</b></a> {subtitle} <ul><li><b>Credits:</b> {credits}</li>"
        
        # conditionally add the concise description if it is not blank
        # and if it does not exactly match the subtitle
        if concise_desc and (concise_desc != subtitle):
            resource_str += f"<li><b>Description:</b> {concise_desc}</li>"
        
        resource_str += f"<li><b>Categories:</b> {separator.join(categories)}</li></ul><br>"

    return resource_str

def get_subscriptions(email):
    return Subscription.objects.filter(subscriber_email=email)

def test_email(request):
    return render(request, 'website/subscription_test_email_template.html')

def test_query():
    my_sub = get_subscriptions('marsha11203@yahoo.com')
    get_resources_from_subscriptions(my_sub[0])

def resources_updated(categories):
    subs = Subscription.objects.filter(categories__in=categories)
    print(subs)
