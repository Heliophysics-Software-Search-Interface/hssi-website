import uuid

from django.conf import settings
from django.contrib.syndication.views import Feed
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views import generic
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string

from ..models import FunctionCategory
# from ..admin import isInlit

def selected_resource_context(request):

	function_categories = FunctionCategory.objects.all()

	context = {
		# 'quality_badge_urls': [
		# 	QualitySpec.UNKNOWN.get_img_url(),
		# 	QualitySpec.NEEDS_IMPROVEMENT.get_img_url(),
		# 	QualitySpec.PARTIALLY_MET.get_img_url(),
		# 	QualitySpec.GOOD.get_img_url()
		# ],
		'function_categories': function_categories,
		# 'functionalities': functionalities,
		# 'categories': categories,
		# 'selected_category_ids': selected_category_ids,
		# 'selected_resources': selected_resources,
		# 'related_resource': related_resource,
		# 'sort': sort,
		# 'stop_words': stop_words,
		# 'tool_types': tool_types,
		# 'selected_tooltype_ids': selected_tooltype_ids,
		# 'collections': collections,
		# 'selected_collection_ids': selected_collection_ids,
		# 'selected_collection': selected_collection,
		# 'in_lit_resources': in_lit_resources
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

		if request.GET:
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
			response = JsonResponse(context)
	else:
		context = selected_resource_context(request)
		response = render(request, 'website/published_resources.html', context)

	return response

def FAQ(request):
	return render(request, 'website/FAQ.html', {})

def team(request):
	return render(request, 'website/team.html', {})
