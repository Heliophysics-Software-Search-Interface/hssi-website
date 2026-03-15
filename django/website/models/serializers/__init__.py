
from django.db.models import Model
from rest_framework.serializers import Serializer

from ...models import Software
from . import software

MODEL_SERIALIZER_MAP: dict[type[Model], type[Serializer]] = {
	Software: software.SoftwareSerializer,
}