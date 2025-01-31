from django.conf import settings

def export_vars(request):
    data = {}

    data['HSSI_DOMAIN'] = settings.HSSI_DOMAIN 
    data['HSSI_PROTOCOL'] = settings.HSSI_PROTOCOL

    return data
