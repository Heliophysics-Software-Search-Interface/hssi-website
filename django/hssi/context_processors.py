from django.conf import settings

def export_vars(request):
	data = {}

	data['SITE_DOMAIN'] = settings.SITE_DOMAIN 
	data['SITE_PROTOCOL'] = settings.SITE_PROTOCOL

	# Only emit the Google Analytics tag in production so local/dev traffic
	# doesn't pollute the real analytics data.
	if not settings.DEBUG:
		data['GA_MEASUREMENT_ID'] = settings.GA_MEASUREMENT_ID

	return data
