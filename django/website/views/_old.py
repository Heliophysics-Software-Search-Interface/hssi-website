import uuid, csv, traceback

from datetime import timedelta
from datetime import date as date_package
from itertools import chain 
from threading import Thread
	

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

from django.conf import settings
from django.core.mail import EmailMessage
from django.contrib.syndication.views import Feed
from django.db import models
from django.db.models import Q, F
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views import generic
from django.shortcuts import redirect
from django.template.context_processors import csrf
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string

from crispy_forms.utils import render_crispy_form

from ipware import get_client_ip

from ..forms import FeedbackForm
from ..models import (
	Category, NewsItem, NewsItemStatus, Resource, TeamMember, ToolType, 
	Collection, InLitResource, Submission, SubmissionStatus, QualitySpec,
	FunctionCategory
)
# from ..admin import isInlit


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
		credits_matches = resources.filter(Q(author__icontains=token))
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

	## get related_resource_id from id if provided
	resource_id = request.GET.get('id', None)
	

	selected_category_ids = request.GET.getlist('category')
	selected_tooltype_ids = request.GET.getlist('tooltype')
	selected_collection_ids = request.GET.getlist('collection')
	selected_category_not_ids = request.GET.getlist('category_not')
	selected_tooltype_not_ids = request.GET.getlist('tooltype_not')
	selected_collection_not_ids = request.GET.getlist('collection_not')
	search_terms = request.GET.get('q')
	sort = request.GET.get('sort', 'date')

	selected_resources = Resource.objects.filter(is_published=True)
	categories = Category.objects.filter(parents=None).order_by('index')
	tool_types = ToolType.objects.filter(parents=None) #.order_by('index')
	collections = Collection.objects.filter(parents=None)
	in_lit_resources = InLitResource.objects.filter(is_published=True)
	function_categories = FunctionCategory.objects.all()
	# functionalities = Functionality.objects.filter(category__in=function_categories)
	
	related_resource = None
	selected_collection = None

	if resource_id:
		related_resource = get_object_or_404(Resource, id=resource_id)
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

	# filter out ids with in the negation filters
	if selected_category_not_ids:
		for category_not_id in selected_category_not_ids:
			selected_resources = selected_resources.exclude(categories__id=category_not_id)
			in_lit_resources = in_lit_resources.exclude(categories__id=category_not_id)

	if selected_tooltype_not_ids:
		for tooltype_not_id in selected_tooltype_not_ids:
			selected_resources = selected_resources.exclude(tool_types__id=tooltype_not_id)
			in_lit_resources = in_lit_resources.exclude(tool_types__id=tooltype_not_id)
	
	if selected_collection_not_ids:
		for collection_not_id in selected_collection_not_ids:
			selected_resources = selected_resources.exclude(collections__id=collection_not_id)
			in_lit_resources = in_lit_resources.exclude(collections__id=collection_not_id)

	# default to sort by date by pass through conditions
	if sort == 'name':
		selected_resources = selected_resources.order_by('name')
	else:
		# sort by date
		selected_resources = selected_resources.order_by('-creation_date')

	if in_lit_resources != None:
		in_lit_resources.order_by('name')
	
	stop_words = None
	
	if (not selected_category_ids) and (not selected_tooltype_ids) and (not search_terms):
		# No category or tooltype filters and no search terms set, setting in-lit to None
		in_lit_resources = None

	context = {
		'quality_badge_urls': [
			QualitySpec.UNKNOWN.get_img_url(),
			QualitySpec.NEEDS_IMPROVEMENT.get_img_url(),
			QualitySpec.PARTIALLY_MET.get_img_url(),
			QualitySpec.GOOD.get_img_url()
		],
		'function_categories': function_categories,
		# 'functionalities': functionalities,
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
		'in_lit_resources': in_lit_resources
	}

	return context


def is_request_ajax(request):
	"""
	TODO (DEPRECATED) fix workaround for deprecated ajax request checking, 
	currently this function is a patch for request.is_ajax() being removed from 
	newer django versions
	"""
	req_with: str | None = request.META.get('HTTP_X_REQUESTED_WITH')
	if req_with: return req_with.upper() == 'XMLHTTPREQUEST'
	return False

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
				context['SITE_PROTOCOL'] = settings.SITE_PROTOCOL
				context['SITE_DOMAIN'] = settings.SITE_DOMAIN
				
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
							"Provide Tutorial: " + str(feedback.provide_tutorial)+"\n" \
							"Provide Web App: "+str(feedback.provide_web_app)+"\n" \
							"Relate a Resource: "+ str(feedback.relate_a_resource)+"\n" \
							"Correction Needed: "+ str(feedback.correction_needed)+"\n" \
							"Comments: " + str(feedback.comments),
						to=["admin@my-site.com"],
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

def FAQ(request):
	published_resources = Resource.objects.filter(is_published=True)
	in_lit_resources = InLitResource.objects.filter(is_published=True)
	context = {
		'resources': published_resources,
		'in_lit_resources': in_lit_resources
	}
	return render(request, 'website/FAQ.html', context)


class NewsView(generic.ListView):
	queryset = NewsItem.objects.filter(status=NewsItemStatus.PUBLISH.name).order_by('-published_on')
	template_name = 'website/news.html'

class NewsItemView(generic.DetailView):
	model = NewsItem
	template_name = 'website/news_item.html'

class NewsFeed(Feed):

	title = "News Feed"
	link = "/news/"
	description = "Updates on tools and activities."
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

	team = TeamMember.objects.filter(Q(is_alumnus=False)).order_by('order')
	alumni = TeamMember.objects.filter(Q(is_alumnus=True)).order_by('order')

	context = {
		'team': team,
		'alumni': alumni
	}

	return render(request, 'website/team.html', context)

def export_search_results(request):

	# build the same context as a regular request
	context = selected_resource_context(request)
	
	if context['selected_collection']:
		filename = "{} Collection.csv".format(context['selected_collection'].name)
	else:
		filename = "Search Results.csv"
	
	response = HttpResponse(
		content_type='text/csv',
		headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
	)

	writer = csv.writer(response)
	writer.writerow(['Name', 'Developers', 'Description', 'Code used', 'Link'])

	for resource in context['selected_resources']:
		link = "{}://{}?id={}".format(settings.SITE_PROTOCOL, settings.SITE_DOMAIN, resource.id)
		credits = resource.credits
		if (resource.credits.startswith('<a')):
			idx = credits.find('>') + 1
			credits = credits[idx:]
			idx = credits.find('</a>')
			credits = credits[:idx]

		writer.writerow([resource.name, credits, resource.description, resource.code_languages, link])

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
			writer.writerow([in_lit_resource.name, credits, in_lit_resource.description, in_lit_resource.code_languages, ''])


	return response

