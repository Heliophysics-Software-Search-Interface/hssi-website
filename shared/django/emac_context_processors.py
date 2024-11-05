from django.conf import settings

def export_vars(request):
    data = {}

    data['EMAC_DOMAIN'] = settings.EMAC_DOMAIN 
    data['EMAC_PROTOCOL'] = settings.EMAC_PROTOCOL

    return data
