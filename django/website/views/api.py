from django.http import JsonResponse, HttpRequest
from django.forms.models import model_to_dict

from ..models import Software

def api_view(request: HttpRequest) -> JsonResponse:
    data: Software | None = None
    if len(Software.objects.all()) <= 0:data = None
    else: data = Software.objects.all()[0]

    json_data: dict = data.get_hssi_data_dict() if data else {"Error": "No software found"}
    return JsonResponse(json_data)