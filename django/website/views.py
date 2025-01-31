import os, uuid, csv, requests, traceback
from requests.adapters import HTTPAdapter
from io import StringIO
import re
import pandas as pd

from datetime import timedelta, date
from itertools import chain 
from threading import Thread
    

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

from django.conf import settings
from django.core.mail import EmailMessage
from django.contrib.syndication.views import Feed
from django.db import models
from django.db.models import Q, F
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views import generic
from django.shortcuts import redirect
from django.template.context_processors import csrf
from django.shortcuts import get_object_or_404

from crispy_forms.utils import render_crispy_form

from ipware import get_client_ip

from .analytics import analytics as _analytics # TODO: fix this kludge
from .forms import FeedbackForm, AnalyticsForm #, SubscriptionForm
from .models import Category, NewsItem, NewsItemStatus, PendingSubscriptionNotification, Resource, TeamMember, ToolType, Collection, InLitResource, Submission, SubmissionStatus
from .admin import isInlit
from .subscriptions import *
from . import submissions
from .utils import user_in_curators_group, organized_categories_json, organized_collections_json

def keywords_match_all_tokens(resources, tokens):

    _, resources_by_matched_tokens = keywords_match_some_tokens(resources, tokens)
    result = Resource.objects.none()

    if resources_by_matched_tokens and resources_by_matched_tokens.keys() == set(tokens):
        for matches in resources_by_matched_tokens.values():
            result = result.intersection(matches) if result else matches

    return result

def keywords_match_some_tokens(resources, tokens=[]):

    result = Resource.objects.none()
    resources_by_matched_tokens = {}

    for token in tokens:
        keyword_matches = resources.filter(Q(search_keywords__icontains=token) )
        if keyword_matches:
            resources_by_matched_tokens[token] = keyword_matches
            result = result.union(keyword_matches)

    return result, resources_by_matched_tokens

def names_match_some_tokens(resources, tokens=[]):

    result = Resource.objects.none()
    resources_by_matched_tokens = {}

    for token in tokens:
        name_or_subtitle_matches = resources.filter(Q(name__icontains=token) | Q(subtitle__icontains=token))
        if name_or_subtitle_matches:
            resources_by_matched_tokens[token] = name_or_subtitle_matches
            result = result.union(name_or_subtitle_matches)

    return result, resources_by_matched_tokens

def names_match_all_tokens(resources, tokens):

    _, resources_by_matched_tokens = names_match_some_tokens(resources, tokens)
    result = Resource.objects.none()

    if resources_by_matched_tokens and resources_by_matched_tokens.keys() == set(tokens):
        for matches in resources_by_matched_tokens.values():
            result = result.intersection(matches) if result else matches

    return result

def descriptions_match_some_tokens(resources, tokens):

    result = Resource.objects.none()
    resources_by_matched_tokens = {}

    for token in tokens:
        description_matches = resources.filter(description__icontains=token)
        if description_matches:
            resources_by_matched_tokens[token] = description_matches
            result = result.union(description_matches)

    return result, resources_by_matched_tokens

def descriptions_match_all_tokens(resources, tokens):

    _, resources_by_matched_tokens = descriptions_match_some_tokens(resources, tokens)
    result = Resource.objects.none()

    if resources_by_matched_tokens and resources_by_matched_tokens.keys() == set(tokens):
        for matches in resources_by_matched_tokens.values():
            result = result.intersection(matches) if result else matches

    return result

def credits_match_some_tokens(resources, tokens):
    result = Resource.objects.none()
    resources_by_matched_tokens = {}

    for token in tokens:
        credits_matches = resources.filter(Q(credits__icontains=token) | Q(ascii_credits__icontains=token))
        if credits_matches:
            resources_by_matched_tokens[token] = credits_matches
            result = result.union(credits_matches)
    
    return result, resources_by_matched_tokens

def credits_match_all_tokens(resources, tokens):
    _, resources_by_matched_tokens = credits_match_some_tokens(resources, tokens)
    result = Resource.objects.none()

    if resources_by_matched_tokens and resources_by_matched_tokens.keys() == set(tokens):
        for matches in resources_by_matched_tokens.values():
            result = result.intersection(matches) if result else matches
    
    return result

def selected_resource_context(request):

    related_resource_id = request.GET.get('related_resource', None)

    ## get related_resource_id from citation_id if provided
    citation_id = request.GET.get('cid', None)
    

    selected_category_ids = request.GET.getlist('category')
    selected_tooltype_ids = request.GET.getlist('tooltype')
    selected_collection_ids = request.GET.getlist('collection')
    search_terms = request.GET.get('q')
    sort = request.GET.get('sort', 'date')

    categories = Category.objects.filter(parents=None).order_by('index')
    selected_resources = Resource.objects.filter(is_published=True)
    tool_types = ToolType.objects.filter(parents=None) #.order_by('index')
    collections = Collection.objects.filter(parents=None)
    in_lit_resources = InLitResource.objects.filter(is_published=True)

    related_resource = None
    selected_collection = None
    curators = None

    if citation_id:        
        # related_resource = Resource.objects.get(citation_id=citation_id)
        related_resource = get_object_or_404(Resource, citation_id=citation_id)
        selected_resources = related_resource.related_resources.filter(is_published=True)
        in_lit_resources = None
    ##

    if related_resource_id:
        related_resource = Resource.objects.get(id=related_resource_id)
        selected_resources = related_resource.related_resources.filter(is_published=True)
        in_lit_resources = None

    if selected_category_ids:
        selected_category_ids = list(map(uuid.UUID, selected_category_ids))

        for category_id in selected_category_ids:
            selected_resources = selected_resources.filter(categories__id=category_id)
            in_lit_resources = in_lit_resources.filter(categories__id=category_id)

        selected_resources = selected_resources.distinct()
        in_lit_resources = in_lit_resources.distinct()

    if selected_tooltype_ids:
        selected_tooltype_ids = list(map(uuid.UUID, selected_tooltype_ids))

        for tooltype_id in selected_tooltype_ids:
            selected_resources = selected_resources.filter(tool_types__id=tooltype_id)
            in_lit_resources = in_lit_resources.filter(tool_types__id=tooltype_id)

        selected_resources = selected_resources.distinct()
        in_lit_resources = in_lit_resources.distinct()

    if selected_collection_ids:
        selected_collection_ids = list(map(uuid.UUID, selected_collection_ids))
        # we know there is only going to be one selected collection
        selected_collection_id = selected_collection_ids[0]
        selected_collection = Collection.objects.get(id=selected_collection_id)
        selected_resources = selected_resources.filter(collections__id=selected_collection_id)
        selected_resources = selected_resources.distinct()
        in_lit_resources = None
        curator_objs = TeamMember.objects.filter(collections__id=selected_collection_id)
        curator_strings = []
        for curator in curator_objs:
            if curator.personal_url:
                curator_strings.append(f"<a href='{curator.personal_url}' target='_blank'>{curator.name}</a>")
            else:
                curator_strings.append(curator.name)
        curators = ", ".join(curator_strings)

    # check if user is curator
    is_curator = user_in_curators_group(request.user)
    # don't let non-curators sort by curation date
    if not is_curator and sort == 'curated':
        sort='date'
    
    # default to sort by date by pass through conditions
    if sort == 'name':
        selected_resources = selected_resources.order_by('name')
    elif sort == 'curated':
        curated_resources = list(selected_resources.filter(submission__last_curated_date__isnull=False).all())
        uncurated_resources = list(selected_resources.filter(submission__last_curated_date__isnull=True).all())

        if in_lit_resources != None:
            curated_inlit = list(in_lit_resources.filter(submission__last_curated_date__isnull=False).all())
            for res in curated_inlit:
                res.is_inlit = True
            uncurated_inlit = list(in_lit_resources.filter(submission__last_curated_date__isnull=True).all())
            for res in uncurated_inlit:
                res.is_inlit = True
            curated_resources.extend(curated_inlit)
            uncurated_resources.extend(uncurated_inlit)
            in_lit_resources = None
        
        curated_resources.sort(key=lambda res: res.submission.last_curated_date)
        uncurated_resources.sort(key=lambda res: res.last_modification_date)
        selected_resources = list(chain(uncurated_resources, curated_resources))
        
    else:
        # sort by date
        selected_resources = selected_resources.order_by('-last_modification_date')

    if in_lit_resources != None:
        in_lit_resources.order_by('name')

    
    stop_words = None
    if search_terms:
        word_tokens = set(word_tokenize(search_terms.lower().replace('-', ' ')))
        stop_words = set(stopwords.words('english'))
        tokens = [token for token in word_tokens if token.isalnum() and not token in stop_words]
        stop_words = word_tokens.intersection(stop_words)
    
        credits_match_some, _ = credits_match_some_tokens(selected_resources, tokens)
        credits_match_all = credits_match_all_tokens(selected_resources, tokens)
        keywords_match_some, _ = keywords_match_some_tokens(selected_resources, tokens)
        keywords_match_all = keywords_match_all_tokens(selected_resources, tokens)
        names_match_all = names_match_all_tokens(selected_resources, tokens)
        names_match_some, _ = names_match_some_tokens(selected_resources, tokens)
        descriptions_match_all = descriptions_match_all_tokens(selected_resources, tokens)
        descriptions_match_some, _ = descriptions_match_some_tokens(selected_resources, tokens)

        inlit_credits_some, _ = credits_match_some_tokens(in_lit_resources, tokens)
        inlit_credits_all = credits_match_all_tokens(in_lit_resources, tokens)
        inlit_keywords_some, _ = keywords_match_some_tokens(in_lit_resources, tokens)
        inlit_keywords_all = keywords_match_all_tokens(in_lit_resources, tokens)
        inlit_names_all = names_match_all_tokens(in_lit_resources, tokens)
        inlit_names_some, _ = names_match_some_tokens(in_lit_resources, tokens)

        # Apply search result weighting, ordering

        names_match_all = names_match_all.difference(credits_match_all)
        keywords_match_all = keywords_match_all.difference(credits_match_all, names_match_all)
        descriptions_match_all = descriptions_match_all.difference(credits_match_all, names_match_all, keywords_match_all)

        credits_match_some = credits_match_some.difference(credits_match_all, keywords_match_all, names_match_all, descriptions_match_all)
        keywords_match_some = keywords_match_some.difference(credits_match_all, keywords_match_all, names_match_all, descriptions_match_all, credits_match_some)
        names_match_some = names_match_some.difference(credits_match_all, keywords_match_all, names_match_all, descriptions_match_all, credits_match_some, keywords_match_some)
        descriptions_match_some = descriptions_match_some.difference(credits_match_all, keywords_match_all, names_match_all, descriptions_match_all, credits_match_some, keywords_match_some, names_match_some)
        
        selected_resources = {} if not tokens else \
            list(chain(credits_match_all, keywords_match_all, names_match_all, descriptions_match_all, credits_match_some, keywords_match_some, names_match_some, descriptions_match_some))

        inlit_keywords_all = inlit_keywords_all.difference(inlit_credits_all)
        inlit_names_all = inlit_names_all.difference(inlit_credits_all, inlit_keywords_all)
        inlit_credits_some = inlit_credits_some.difference(inlit_credits_all, inlit_keywords_all, inlit_names_all)
        inlit_keywords_some = inlit_keywords_some.difference(inlit_credits_all, inlit_keywords_all, inlit_names_all, inlit_credits_some)
        inlit_names_some = inlit_names_some.difference(inlit_credits_all, inlit_keywords_all, inlit_names_all, inlit_credits_some, inlit_keywords_some)

        in_lit_resources = {} if not tokens else \
            list(chain(inlit_credits_all, inlit_keywords_all, inlit_names_all, inlit_credits_some, inlit_keywords_some, inlit_names_some))
    
    if (not selected_category_ids) and (not selected_tooltype_ids) and (not search_terms):
        # No category or tooltype filters and no search terms set, setting in-lit to None
        in_lit_resources = None


    context = {
        'categories': categories,
        'selected_category_ids': selected_category_ids,
        'selected_resources': selected_resources,
        'related_resource': related_resource,
        'sort': sort,
        'stop_words': stop_words,
        'tool_types': tool_types,
        'selected_tooltype_ids': selected_tooltype_ids,
        'collections': collections,
        'selected_collection_ids': selected_collection_ids,
        'selected_collection': selected_collection,
        'in_lit_resources': in_lit_resources,
        'curators': curators,
        'is_curator': is_curator
    }

    return context

def is_request_ajax(request):
    """
    TODO (DEPRECATED) fix workaround for deprecated ajax request checking, 
    currently this function is a patch for request.is_ajax() being removed from 
    newer django versions
    """
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHTTPREQUEST'

def published_resources(request):

    context = {}
    response = None

    if is_request_ajax(request):
        feedback_form = None
        resource_id = None

        if request.GET:
            resource_id = request.GET.get('resource_id')
            if resource_id:
                resource_name = Resource.objects.get(id=uuid.UUID(resource_id)).name
                context['resource_name'] = resource_name
                feedback_form = FeedbackForm(initial={'resource_id_temp' : resource_id})
            else:
                # build the same context as a regular request
                context = selected_resource_context(request)
                
                # add the protocol and domain settings to the context
                context['HSSI_PROTOCOL'] = settings.HSSI_PROTOCOL
                context['HSSI_DOMAIN'] = settings.HSSI_DOMAIN
                
                # render the list of included resources
                resource_list = render_to_string('website/resource_list.html', context, request)

                # reset the context with what we want to send back
                context = {}

                # add the HTML string back onto the context,
                # same as how the feedback form is set up below
                context['resource_content'] = resource_list 
                
        else:
            resource_id_temp = None
            resource_id_temp = request.POST.get('resource_id_temp')
            
            resource_id = uuid.UUID(resource_id_temp)
            cleaned_POST = request.POST.copy()
            cleaned_POST.pop('resource_id_temp')
            feedback_form = FeedbackForm(cleaned_POST)

            if feedback_form.has_changed():
                if feedback_form.is_valid():
                    client_ip, is_routable = get_client_ip(request)
                    if client_ip is not None and is_routable:
                        feedback_form.submitter_ip_address = client_ip
                    
                    feedback = feedback_form.save()
                    feedback_form = None
                    feedback.resource = Resource.objects.get(id=resource_id)
                    feedback.save()
                    # call method here to send email
                    message = EmailMessage(
                        subject="New Feedback for %s" % feedback.resource.name,
                        body="Resource: "+str(feedback.resource.name)+"\n" \
                            "Feedback Date: "+str(feedback.feedback_date)+"\n" \
                            "Submitter IP: "+str(feedback.submitter_ip_address)+"\n" \
                            "Provide Demo Video: "+str(feedback.provide_demo_video)+"\n" \
                            "Provide Jupyter Tutorial: " + str(feedback.provide_tutorial)+"\n" \
                            "Provide Web App: "+str(feedback.provide_web_app)+"\n" \
                            "Relate a Resource: "+ str(feedback.relate_a_resource)+"\n" \
                            "Correction Needed: "+ str(feedback.correction_needed)+"\n" \
                            "Comments: " + str(feedback.comments),
                        to=["REDACTED"],
                    )

                    try:
                        message.send(fail_silently=False)
                    except:
                        print("Feedback email failed to send")
                else:
                    print(f"FeedbackForm is invalid:{feedback_form}")
            else:
                feedback_form = None
            

        if feedback_form:
            context['rendered_form'] = render_crispy_form(feedback_form, context=csrf(request))

        response = JsonResponse(context)
    else:
        context = selected_resource_context(request)
        response = render(request, 'website/published_resources.html', context)

    return response

os.environ["ADS_DEV_KEY"] = settings.ADS_DEV_KEY

def contact_all(request):
    """
    Run a mass contact.
    Contacts all submissions that haven't been contacted in 3 months. 
    """
    class Contact_all_thread(Thread):
        def run(self):
            err_msg = ''
            first_in_lit_counter = ""
            first_non_in_lit_counter = ""
            new_in_lit_counter = ""
            second_non_in_lit_counter = ""
            final_in_lit_counter = ""
            final_non_in_lit_counter = ""
            total_contacts = 0
            submissionList = Submission.objects.all()
            for submission in submissionList:
                try:
                    if submission.status == SubmissionStatus.FIRST_CONTACT.name:
                        if isInlit(submission):
                            submissions.send_contact_email(submission, SaveType.INITIALINLITCONTACT)
                            first_in_lit_counter += f"   - {submission.name}\n"
                        else:
                            submissions.send_contact_email(submission, SaveType.FIRSTCONTACT)
                            first_non_in_lit_counter += f"   - {submission.name}\n" 
                        # Updates the contacted_date of the contacted submissions and increments contact_count
                        submission.status = SubmissionStatus.CONTACTED.name
                        submission.contact_count += 1
                        submission.date_contacted = timezone.now()
                        submission.save()
                        total_contacts += 1
                    elif (submission.status == SubmissionStatus.CONTACTED.name) and (date.today() - submission.date_contacted > timedelta(days=89)):
                        if isInlit(submission):
                            if submission.contact_count == 1:
                                submissions.send_contact_email(submission, SaveType.SECONDINLITCONTACT)
                                submission:Submission
                                submission.make_in_lit_resource()
                                submission.status = SubmissionStatus.IN_LITERATURE.name
                                new_in_lit_counter += f"   - {submission.name}\n"
                            else:
                                submissions.send_contact_email(submission, SaveType.FINALINLITCONTACT)
                                submission:Submission
                                submission.make_in_lit_resource()
                                submission.status = SubmissionStatus.IN_LITERATURE.name
                                new_in_lit_counter += f"   - {submission.name}\n"
                        else:
                            if submission.contact_count == 1:
                                submissions.send_contact_email(submission, SaveType.RECONTACT)
                                second_non_in_lit_counter += f"   - {submission.name}\n"
                            else:
                                submissions.send_contact_email(submission, SaveType.FINALCONTACT)
                                submission.status = SubmissionStatus.REJECTED_ABANDONED.name
                                submission.status_notes = "Rejected by the monthly Mass Contact. The resource is not in the literature and the developer has been contacted at least 3 times.\n" + submission.status_notes
                                final_non_in_lit_counter += f"   - {submission.name}\n"
                        submission.contact_count += 1
                        submission.date_contacted = timezone.now()
                        submission.save()
                        total_contacts += 1
                    elif (submission.status == SubmissionStatus.IN_LITERATURE.name and submission.contact_count == 2) and (date.today() - submission.date_contacted > timedelta(days=89)):
                        submissions.send_contact_email(submission, SaveType.FINALINLITCONTACT)
                        submission.contact_count += 1
                        submission.date_contacted = timezone.now()
                        submission.save()
                        final_in_lit_counter += f"   - {submission.name}\n"
                        total_contacts += 1
                except Exception as err:
                    msg = f'Contact failed for Resource {submission.name}\n'
                    msg += f'Email Used: {submission.submitter_email}\n'
                    msg += ''.join(traceback.TracebackException.from_exception(err).format()) + '\n'
                    print(msg)
                    err_msg+= msg+'\n'

            print("Mass contact done")
            body = f"Number of submissions contacted: {total_contacts} \n \n \n"
            if first_in_lit_counter + first_non_in_lit_counter:
                body += f"First contacts sent to: \n {first_in_lit_counter + first_non_in_lit_counter} \n"
            if second_non_in_lit_counter:
                body += f"Followup contacts sent to: \n {second_non_in_lit_counter} \n"
            if new_in_lit_counter:
                body += f"New In-Lit Resources created: \n {new_in_lit_counter} \n"
            if final_non_in_lit_counter:
                body += f"Submissions marked as Rejected/Abandoned: \n {final_non_in_lit_counter} \n"
            if final_in_lit_counter:
                body += f"Final followups sent for the In-Lit Resources: \n {final_in_lit_counter} \n"
            if err_msg != '':
                print("Error in mass contact")
                message = EmailMessage(
                    subject="HSSI submission mass contact",
                    body=f"There was an error with the mass contact!\n{err_msg} \n" + body,
                    to=["REDACTED@nasa.gov"],
                )
                try:
                    message.send(fail_silently=False)
                except:
                    print("Mass contact failed and email failed to send")
                else:
                    print("Mass contact failed and email sent")
            else:
                print("Mass contact successful")
                message = EmailMessage(
                    subject="HSSI submission mass contact",
                    body= "Mass submission contact was done successfully! \n" + body,
                    to=["REDACTED@nasa.gov"],
                )
                try:
                    message.send(fail_silently=False)
                except:
                    print("Mass contact failed and email failed to send")
                else:
                    print("Mass contact failed and email sent")

    Contact_all_thread().start()
    
    return redirect('/')

def ascl_scraper(request):
    """
    Run the ASCL ID scraper for each resource
    """
    class ASCL_scraper_thread(Thread):
        def run(self):
            err_msg = ''
            resources = Resource.objects.all()
            for resource in resources:
                if resource.ascl_id == "":
                    print(f'Getting ASCL ID for {resource.name}')
                    try:
                        ascl_id = resource.query_ascl_id()
                        if ascl_id != "":
                            print(f'ASCL ID {ascl_id} found for {resource.name}')
                            resource.ascl_id = ascl_id
                            resource.submission.ascl_id = ascl_id
                            resource.save()
                            resource.submission.save()
                    except RuntimeError as err:
                        err_msg += ''.join(traceback.TracebackException.from_exception(err).format()) + '\n'
            print('ASCL Scraper Done')
            if err_msg != '':
                print("Validation Errors in ASCL scraper")
                message = EmailMessage(
                    subject="HSSI ASCL Citation Scraper Had Validation Errors",
                    body=f"There was a problem with the ASCL scraper!\n{err_msg}",
                    to=["REDACTED@nasa.gov"],
                )
                try:
                    message.send(fail_silently=False)
                except:
                    print("ASCL citation scraper failed and email failed to send")
                else:
                    print("ASCL citation scraper failed and email sent")
    ASCL_scraper_thread().start()

    return redirect('/')

def run_analytics(request):
    analytics = _analytics.Analytics()
    context = {}

    if request.method == 'GET':
        form = AnalyticsForm()
        context['form'] = form
    else:
        form = AnalyticsForm(request.POST)
        context['form'] = form

        error_string = "Plots which failed: "
        if form.is_valid():
            # inputs = form.cleaned_data
            all_val = form.cleaned_data.get("remake_all")
            # yt_val = form.cleaned_data.get("youtube_analytics")
            if all_val:
                analytics.make_clicks_per_tool()
                analytics.make_exit_clicks_by_category()
                analytics.make_visits_over_time()
                analytics.make_weekly_visits()
                top_engagement_text, top_engagement_time, top_engagement_engagements, bot_engagement_text, bot_engagement_time, bot_engagement_engagements = analytics.make_twitter_analytics()
                # print(top_engagement_text, top_engagement_time, top_engagement_engagements)
                context["top_tweets"] = zip(top_engagement_text, top_engagement_time, top_engagement_engagements)
                # print(bot_engagement_text, bot_engagement_time, bot_engagement_engagements)
                context["bot_tweets"] = zip(bot_engagement_text, bot_engagement_time, bot_engagement_engagements)
                analytics.make_social_traffic()
                analytics.make_RSS_report()
                analytics.make_tools_per_category()
                analytics.make_tools_per_coding_language()
                analytics.make_new_visitors_over_time()
                analytics.make_new_visitors_fraction_over_time()
                analytics.make_n_tools()
                analytics.subs_over_time()
                # try:
                #     analytics.make_clicks_per_tool()
                # except:
                #     error_string += "clicks per tool, "
                #     pass
                # try:
                #     analytics.make_visits_over_time()
                # except:
                #     error_string += "visits over time, "
                #     pass
                # try:
                #     analytics.make_weekly_visits()
                # except:
                #     error_string += "weekly visits over time, "
                #     pass
                # try:
                #     analytics.make_exit_clicks_by_category()
                # except:
                #     error_string += "exit clicks by category, "
                #     pass
                # try:
                #     top_engagement_text, top_engagement_time, top_engagement_engagements, bot_engagement_text, bot_engagement_time, bot_engagement_engagements = analytics.make_twitter_analytics()
                #     context["top_tweets"] = zip(top_engagement_text, top_engagement_time, top_engagement_engagements)
                #     context["bot_tweets"] = zip(bot_engagement_text, bot_engagement_time, bot_engagement_engagements)
                # except:
                #     error_string += "twitter, "
                #     pass
                # try:
                #     analytics.make_social_traffic()
                # except:
                #     error_string += "social traffic, "
                #     pass
                # try:
                #     analytics.make_RSS_report()
                # except:
                #     error_string += "RSS, "
                #     pass
                # try:
                #     analytics.make_tools_per_category()
                # except:
                #     error_string += "tools per category, "
                #     pass
                # try:
                #     analytics.make_tools_per_coding_language()
                # except:
                #     error_string += "tools per coding language, "
                #     pass
                # try:
                #     analytics.make_new_visitors_over_time()
                # except:
                #     error_string += "new visitors over time, "
                #     pass
                # try:
                #     analytics.make_new_visitors_fraction_over_time()
                # except:
                #     error_string += "new visitors fraction, "
                #     pass
                # try:
                #     analytics.make_n_tools()
                # except:
                #     error_string += "n tools, "
                #     pass
                # try:
                #     analytics.subs_over_time()
                # except:
                #     error_string += "n subs, "
                #     pass
                # try:
                #     analytics.make_youtube_analytics()
                # except:
                #     error_string += "youtube, "
                #     pass
            # if inputs["clicks_per_tool"] == True:
            #     analytics.make_clicks_per_tool()
            # if inputs["new_user_fraction"] == True:
            #     analytics.make_new_visitors_fraction_over_time()
            # if inputs["visits_over_time"] == True:
            #     analytics.make_visits_over_time()
            # if inputs["weekly_visits"] == True:
            #     analytics.make_weekly_visits()
            # if inputs["exit_clicks_by_category"] == True:
            #     analytics.make_exit_clicks_by_category()
            # if inputs["twitter_analytics"] == True:
            #     top_engagement_text, top_engagement_time, top_engagement_engagements, bot_engagement_text, bot_engagement_time, bot_engagement_engagements = analytics.make_twitter_analytics()
            #     context["top_tweets"] = zip(top_engagement_text, top_engagement_time, top_engagement_engagements)
            #     context["bot_tweets"] = zip(bot_engagement_text, bot_engagement_time, bot_engagement_engagements)
            # if inputs["social_traffic"] == True:
            #     analytics.make_social_traffic()
            # if inputs["RSS_report"] == True:
            #     analytics.make_RSS_report()
            # if inputs["youtube_analytics"] == True:
            #     analytics.make_youtube_analytics()
            # if inputs["tools_per_category"] == True:
            #     analytics.make_tools_per_category()
            # if inputs["tools_per_coding_language"] == True:
            #     analytics.make_tools_per_coding_language()
            # if inputs["new_visitors_over_time"] == True:
            #     analytics.make_new_visitors_over_time()
            # if inputs["n_tools"] == True:
            #     analytics.make_n_tools()

            # JPR 2023-04-24: Disabling youtube analytics due to error in analytix package.
            # if yt_val:
            #     analytics.make_youtube_analytics()

            print(error_string)
            context["error_string"] = error_string

        else:
            print(form.errors)

    if is_request_ajax(request):
        context['rendered_form'] = form.as_table()
        response = JsonResponse(context)
    else:
        response = render(request, "website/analytics.html", context)

    return response

def run_io_diagram(request):
    return render(request, "website/io_diagram.html")

def FAQ(request):
    published_resources = Resource.objects.filter(is_published=True)
    in_lit_resources = InLitResource.objects.filter(is_published=True)
    context = {
        'resources': published_resources,
        'in_lit_resources': in_lit_resources
    }
    return render(request, 'website/FAQ.html', context)

def seminars(request):
    return render(request, 'website/seminars.html')

def developers(request):
    return render(request, 'website/for_developers.html')

class NewsView(generic.ListView):
    queryset = NewsItem.objects.filter(status=NewsItemStatus.PUBLISH.name).order_by('-published_on')
    template_name = 'website/news.html'

class NewsItemView(generic.DetailView):
    model = NewsItem
    template_name = 'website/news_item.html'

class NewsFeed(Feed):

    title = "HSSI News"
    link = "/news/"
    description = "Updates on HSSI tools and activities."
    item_template = "website/news_item.html"

    def items(self):
        return NewsItem.objects.order_by('-published_on')[:5]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.content

    def item_link(self, item):
        return reverse('website:news_item', args=[item.pk])

def team(request):

    team = TeamMember.objects.filter(Q(is_alumnus=False,is_curator=False)).order_by('order')
    alumni = TeamMember.objects.filter(Q(is_alumnus=True)).order_by('order')
    curators = TeamMember.objects.filter(Q(is_alumnus=False,is_curator=True)).order_by('order')

    categories = Category.objects.filter(parents=None).order_by('index')
    collections = Collection.objects.filter(parents=None)

    context = {
        'team': team,
        'alumni': alumni,
        'curators': curators,
        'categories': categories,
        'collections': collections
    }

    return render(request, 'website/team.html', context)

def export_search_results(request):

    # build the same context as a regular request
    context = selected_resource_context(request)
    
    if context['selected_collection']:
        filename = "HSSI {} Collection.csv".format(context['selected_collection'].name)
    else:
        filename = "HSSI Search Results.csv"
    
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
    )

    writer = csv.writer(response)
    writer.writerow(['Name', 'Developers', 'Description', 'Code used', 'HSSI Link', 'ADS Link'])

    for resource in context['selected_resources']:
        link = "{}://{}?cid={}".format(settings.HSSI_PROTOCOL, settings.HSSI_DOMAIN, resource.citation_id)
        credits = resource.credits
        if (resource.credits.startswith('<a')):
            idx = credits.find('>') + 1
            credits = credits[idx:]
            idx = credits.find('</a>')
            credits = credits[:idx]

        writer.writerow([resource.name, credits, resource.description, resource.code_languages, link, resource.ads_abstract_link])

    if context['in_lit_resources']:
        writer.writerow([])
        writer.writerow(['Other rsources in the literature:'])

        for in_lit_resource in context['in_lit_resources']:
            credits = resource.credits
            if (resource.credits.startswith('<a')):
                idx = credits.find('>') + 1
                credits = credits[idx:]
                idx = credits.find('</a>')
                credits = credits[:idx]
            writer.writerow([in_lit_resource.name, credits, in_lit_resource.description, in_lit_resource.code_languages, '', in_lit_resource.ads_abstract_link])


    return response

def scan_links(request):
    context = {}
    response = None

    published_resources = Resource.objects.filter(is_published=True)

    resource_list = []

    for resource in published_resources:
        resource_list.append({
            'id': resource.id,
            'name': resource.name,
            'logo_link': resource.logo_link,
            'about_link': resource.about_link,
            'ads_abstract_link': resource.ads_abstract_link,
            'jupyter_link': resource.jupyter_link,
            'download_link': resource.download_link,
            'download_data_link' : resource.download_data_link,
            'launch_link': resource.launch_link,
            'demo_link': resource.demo_link,
            'discuss_link': resource.discuss_link
        })

    if is_request_ajax(request):
        
        resource_id = request.GET.get('id')

        resource = next((res for res in resource_list if res['id'] == uuid.UUID(resource_id)), None)

        resource_found = False

        if resource is not None:
            resource_found = True
            link_properties = [
                'logo_link',
                'about_link',
                'ads_abstract_link',
                'jupyter_link',
                'download_link',
                'download_data_link',
                'launch_link',
                'demo_link',
                'discuss_link'
            ]

            session = requests.Session()
            session.mount('http://', HTTPAdapter(max_retries=3))
            session.mount('https://', HTTPAdapter(max_retries=3))

            for prop_name in link_properties:
                if (resource[prop_name]):
                    status_prop = prop_name + '_status'
                    try:
                        link_response = session.get(resource[prop_name])
                        resource[status_prop] = link_response.status_code
                    except Exception as ex:
                        resource[status_prop] = type(ex).__name__


        context = {
            'resource': resource
        }
        links_table = render_to_string('website/resource_links_table.html', context)
        context = {
            'links_table': links_table,
            'id': resource_id,
            'resource_found': resource_found
        }
        response = JsonResponse(context)
    else:
        context = {
            'resource_list': resource_list
        }
        response = render(request, 'website/scan_links.html', context)
    
    return response

from django.db.models.signals import post_save
from website.admin import export_database_changes
import sys
def cid_seed(request):
    print("disabling database exports)")
    post_save.disconnect(export_database_changes)
    missingCid = Resource.objects.filter(citation_id="")
    updated = []
    
    today = date.today()
    yearMon = today.strftime("%y%m")
    
    for resource in missingCid:
        currentCitations = Resource.objects.filter(
                citation_id__startswith =f"{yearMon}-" 
            ).order_by("citation_id")

        newCitationStr = ""
        if len(currentCitations) == 0:
            #first resource in this month so start with 001
            newCitationStr =  f"{yearMon}-001"
        else:
            latest = currentCitations.last()
            highestNumber = int ( latest.citation_id.split("-")[1] )
            newCitationNumber = highestNumber + 1
            newCitationStr =  f"{yearMon}-{newCitationNumber:03d}"
        
        resource.citation_id = newCitationStr
        resource.save()
        print(f"Updated citation id on {resource.name} to {resource.citation_id}\n")
        sys.stdout.flush()
        updated.append(resource)

    context = {
        "updated": updated        
    }
    print("re-enabling database exports")
    post_save.connect(export_database_changes)
    return render(request, 'website/cid_seed.html', context)

def ADS_endpoint(request):
    resources = Resource.objects.filter(is_published=True)
    data = {}
    for resource in resources:
        cid = resource.citation_id
        ascl_id = resource.ascl_id
        bibcode = resource.get_bibcode()
        link = resource.get_absolute_url()
        name = resource.name
        data[cid] = {
            'bibcode':bibcode,
            'ascl_id':ascl_id,
            'link':link,
            'name':name
        }
    return JsonResponse(data)

from hssi.recaptcha_auth_forms import RecaptchaAuthenticationForm
from django.contrib.auth import login
def curator_login(request):

    if request.method == 'POST':
        next = request.POST.get('next')
        form = RecaptchaAuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            if next == None or next == '':
                next = '/'
            return redirect(next)
    else:
        form = RecaptchaAuthenticationForm()
        next = request.GET.get('next')
    
    context = {
        'form': form,
        'user': request.user,
    }
    if next != None:
        context['next'] = next
        
    return render(request, 'website/curator_login.html', context)

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Button, Submit
class CurateForm(ModelForm):
    class Meta:
        model = Submission
        fields = [
            'concise_description',
            'search_keywords',
            'related_tool_string',
            'categories',
            'collections'
        ]
        help_texts = Submission.help_texts
        labels = Submission.labels
        widgets = {
            'categories': CheckboxSelectMultiple(),
            'collections': CheckboxSelectMultiple()
        }
    
    def __init__(self, *args, **kwargs):
        super(CurateForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_class = 'form'
        self.helper.form_id = 'id-submission_form'
        self.helper.form_method = 'POST'

from ipware import get_client_ip
from .submissions import submission_was_saved
from django.contrib.auth.decorators import login_required, user_passes_test
@login_required
@user_passes_test(user_in_curators_group)
def curate(request):
    
    cid = request.GET.get('cid')
    id = request.GET.get('id')
    
    curate_form = None
    resource = None
    
    # if it's a published resource we refer to it using the CID,
    # if it's an in-lit (not yet published), we have no CID
    # therefore have to use the regular ID
    if (cid):
        resource = get_object_or_404(Resource, citation_id=cid)
    elif (id):
        resource = get_object_or_404(InLitResource, id=id)
    else:
        return redirect('/curators')

    submission = resource.submission
    selected_category_ids = []
    selected_collection_ids = []

    if request.POST:
        curate_form = CurateForm(request.POST, request.FILES, instance=Submission.objects.get(id=submission.id))

        if curate_form.is_valid():

            client_ip, is_routable = get_client_ip(request)
            if client_ip is not None and is_routable:
                curate_form.submitter_ip_address = client_ip

            # have to get the old values of the collections and categories
            # before saving the form because saving the form will update
            # the relationships even on the old_submission
            old_submission = Submission.objects.get(pk=submission.id)
            old_categories = ", ".join(old_submission.categories.all().values_list('name', flat=True))
            old_collections = ", ".join(old_submission.collections.all().values_list('name', flat=True))

            new_submission = curate_form.save()

            changed_fields = {}

            submission_class = new_submission.__class__
            fields = submission_class._meta.get_fields()

            for field in fields:
                field_name = field.name
                try:
                    old_val = ""
                    new_val = ""

                    if field_name == "categories":
                        old_val = old_categories
                        new_val = ", ".join(new_submission.categories.all().values_list('name', flat=True))
                    elif field_name == "collections":
                        old_val = old_collections
                        new_val = ", ".join(new_submission.collections.all().values_list('name', flat=True))
                    else:
                        old_val = getattr(old_submission, field_name)
                        new_val = getattr(new_submission, field_name)
                    
                    if old_val != new_val:
                        changed_fields[field_name] = [old_val, new_val]
                    
                except Exception as ex:  # Catch field does not exist exception
                    pass
            
            new_submission.last_modification_date = timezone.now()
            new_submission.has_unsynced_changes = True
            new_submission.curator_lock = request.user
            new_submission.last_curated_date = timezone.now()
            new_submission.last_curated_by = request.user.username
            new_submission.all_curators.add(request.user)

            if hasattr(request.user, 'team_member'):
                new_submission.last_curated_by = request.user.team_member.name
            elif request.user.first_name and request.user.last_name:
                new_submission.last_curated_by = f"{request.user.first_name} {request.user.last_name}"
            else:
                new_submission.last_curated_by = "-"

            new_submission.save()

            save_type = SaveType.CURATE
            submission_was_saved(new_submission, save_type, changed_fields, request.user)

            request.session['submission_id'] = str(new_submission.id)
            return redirect('/curate/success/')
    else:
        for category in submission.categories.all():
            selected_category_ids.append(str(category.id))

        for collection in submission.collections.all():
            selected_collection_ids.append(str(collection.id))

        locked = False
        if (submission.curator_lock != None and submission.curator_lock != request.user):
            locked = True
        
        curate_form = CurateForm(instance=submission)

        form_action_url = '/curate/'
        if (cid):
            form_action_url = f'/curate/?cid={cid}'
        elif (id):
            form_action_url = f'/curate/?id={id}'

        curate_form.helper.form_action = str(form_action_url)

        if (not locked):
            curate_form.helper.add_input(Submit('save', 'Save', css_class='hollow button save'))
        curate_form.helper.add_input(Button('cancel', 'Cancel', css_class='hollow button cancel', onclick=f"window.location.href='/';"))
    
    category_hierarchy_json, category_names_by_id_json = organized_categories_json()
    collection_hierarchy_json, collection_names_by_id_json = organized_collections_json()
    
    context = {
        'submission': submission,
        'curate_form': curate_form,
        'locked': locked,
        'category_hierarchy_json': category_hierarchy_json,
        'category_names_by_id_json': category_names_by_id_json,
        'selected_category_ids_json': json.dumps(selected_category_ids),
        'collection_hierarchy_json': collection_hierarchy_json,
        'collection_names_by_id_json': collection_names_by_id_json,
        'selected_collection_ids_json': json.dumps(selected_collection_ids)
    }
    return render(request, 'website/curate.html', context)

def curate_success(request):
    submission_id = uuid.UUID(request.session.get('submission_id'))
    submission = Submission.objects.get(id=submission_id)
    context = {
        'submission': submission
    }
    return render(request, 'website/curate_success.html', context)

def git_fetch_version(request):
    """
    Fetches the current version numbers for GitHub repositories and the latest release notes.
    Updates the version numbers for the resources (if available). Saves the latest release notes to the submissions.
    For resources that were updated, it emails us a csv file with the changes and links to send out subscription alerts.
    If there are any errors with the version fetching, it emails us a report of the errors.
    """
    def same_ver(ver1, ver2):
        """
        Compares two version numbers and returns True if they are the same, False otherwise.
        It has checks that make it so that e.g. v1.1 and 1.1.0 are the same.
        """
        clean_ver1 = re.sub("[^\d\.]", "", ver1).strip('.').split('.')
        clean_ver2 = re.sub("[^\d\.]", "", ver2).strip('.').split('.')
        while len(clean_ver1)>len(clean_ver2):
            clean_ver2.append('0')
        while len(clean_ver2)>len(clean_ver1):
            clean_ver1.append('0')
        return clean_ver1 == clean_ver2
    class git_fetch_version_thread(Thread):
        def _git_helper(self, resource, n_failed, err_msg, git_token, updates_dict):
            """
            This function does the heavy lifting for the github version fetching.
            The view basically calls this for each resource in the database then compiles it all.
            """
            # Check that this resource has a Github repository download_link.
            if resource.download_link and 'github.com' in resource.download_link:
                try:
                    # Extracting username and repository name from the GitHub link
                    elems = resource.download_link.strip('/').split('/')
                    github_user = elems[3]
                    repo_name = elems[4]
                    # Making a GET request to the GitHub API to get access to the resource information
                    releases = requests.get(f"https://api.github.com/repos/{github_user}/{repo_name}/releases",
                                            auth=('GSFC-HSSI', git_token)).json()
                    # Check if there were any published releases to the GitHub repo, and pull the latest one
                    if releases and releases[0]['html_url']:
                        # Pull the info we want
                        old_version = resource.version
                        new_version = f"{releases[0]['html_url'].strip('/').split('/')[-1]}"
                        if not(same_ver(old_version, new_version)):
                            version_message = f"{releases[0]['body'].strip('#').split('#')[0]}"
                            # Update version numbers for both the submission and the resource
                            resource.version = new_version
                            submission = resource.submission
                            submission:Submission
                            submission.version = new_version
                            # Add the update note to the submission
                            submission.github_release = version_message
                            submission.save()
                            resource.save()
                            if old_version:
                                version_date = f"{releases[0]['published_at'][:10]}"
                                version_change = old_version + " --> " + new_version
                                version_message_short = version_message[:min(300, len(version_message))]
                                if len(version_message_short)==300:
                                    version_message_short += '...'
                                # Create the link for changing the message AND notifying subscribers
                                send_alert_link = f'{settings.HSSI_PROTOCOL}://{settings.HSSI_DOMAIN}/github_release_edit/{resource.submission.id}/'
                                # Compile the information and add it to the csv to be sent
                                updates_dict["Resource"].append(resource.name)
                                updates_dict["New Version Date"].append(version_date)
                                updates_dict["Version Change"].append(version_change)
                                updates_dict["Release Message"].append(version_message_short)
                                updates_dict["Alert subscribers"].append(send_alert_link)
                except Exception as err:
                    # If an error occurs then save the message to compile all of them and email them to us
                    n_failed.append(1)
                    msg = f'Fetching version failed for resource {resource.name}\n'
                    # msg += f'Github API link used: https://api.github.com/repos/{github_user}/{repo_name}/releases\n'
                    msg += ''.join(traceback.TracebackException.from_exception(err).format()) + '\n'
                    err_msg.append(msg)

        def run(self):
            n_failed = []
            git_token = settings.GITHUB_API_TOKEN
            err_msg = []
            resourceList = Resource.objects.all()
            n_total = len(resourceList)
            # Initialize a dictionary for the info
            updates_dict = {"Resource":[], 
                            "New Version Date":[], 
                            "Version Change":[], 
                            "Release Message":[], 
                            "Alert subscribers":[],
                            }
            for resource in resourceList:
                # Iterate through the resource database and add the info into the dictionary
                self._git_helper(resource, n_failed, err_msg, git_token, updates_dict)
            
            n_failed = sum(n_failed)
            err_msg = '\n'.join(err_msg)

            message = EmailMessage(
                subject="HSSI New Github Versions",
                body='Version fetching report is attached :)',
                to=["REDACTED@nasa.gov"],
            )
            with StringIO() as csvfile:
                # Convert the dictionary to a pandas dataframe
                updates_df = pd.DataFrame(updates_dict)
                # Sort the pandas dataframe and push newer stuff to the top
                updates_df = updates_df.sort_values(by="New Version Date", ascending=False)
                # Convert the pandas dataframe to a csv and attach it to the email
                updates_df.to_csv(csvfile, index=False)
                message.attach('git_versions.csv', csvfile.getvalue(), 'text/csv')
            try:
                message.send(fail_silently=False)
            except:
                print("New Versions fetched but email failed to send.")
            else:
                print("New Versions fetched and email sent!")

            if err_msg != '':
                print("There were errors in the version fetching from GitHub.")
                message = EmailMessage(
                    subject="HSSI Fetching New Github Versions",
                    body=f"There were {n_failed} errors ({n_failed/n_total*100:.1f}%) with the version fetching :'(\n\n\n{err_msg}",
                    to=["REDACTED@nasa.gov"],
                )
                try:
                    message.send(fail_silently=False)
                except:
                    print(f"The Email failed to send. There were {n_failed} errors ({n_failed/n_total*100}%) with the version fetching :'(\n\n\n{err_msg}")
                else:
                    print("The email detailing where the version fetching failed was sent.")
            else:
                print("The version fetching was successful with no errors!")

    git_fetch_version_thread().start()
    
    return redirect('/')

def version_update(request, id):
    """
    This is the view that is triggered by clicking the Save/Submit button on the update alert link for a resource.
    """
    submission = Submission.objects.get(id=id)
    resource = submission.resource
    # Update the mod date to push the resource tile to the top of the home page
    resource.last_modification_date = timezone.now()
    # Push the release message to the resource 
    resource.github_release = submission.github_release
    resource.save()
    # Add resource to the subscription alert queue
    resource_added_categories(resource)

    context = {
        'resource': resource,
        'release': resource.submission.github_release
    }
    return render(request, 'website/update_alert_success.html', context)
