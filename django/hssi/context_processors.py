from django.conf import settings

def export_vars(request):
    data = {}

    data['SITE_DOMAIN'] = settings.SITE_DOMAIN 
    data['SITE_PROTOCOL'] = settings.SITE_PROTOCOL

    return data
