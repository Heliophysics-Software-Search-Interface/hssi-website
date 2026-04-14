""" Utility tools common for serializer submodules """

import enum
from typing import Any

from django.db.models import Model
from django.http.request import QueryDict
from rest_framework.serializers import ModelSerializer

from hssi.camel_case_renderer import JsonSet, decamelize_data
from ...models import HssiModel, Software

_MODEL_SERIALIZER_MAP: dict[type[Model], type[ModelSerializer]] = {}

Q_VIEW: str = "view"

def _register_serializers():
	from .software import Software, SoftwareSerializer
	from .submitter import Submitter, SubmitterSerializer
	from .person import Person, PersonSerializer
	from .organization import Organization, OrganizationSerializer

	serializer_map: dict[type[Model], type[ModelSerializer]] = {
		Software: SoftwareSerializer,
		Submitter: SubmitterSerializer,
		Person: PersonSerializer,
		Organization: OrganizationSerializer,
	}

	for key, val in serializer_map.items():
		_MODEL_SERIALIZER_MAP[key] = val

def get_registered_serializer(model: type[Model]) -> type[ModelSerializer] | None:
	"""Get the serializer associated with the specified model."""
	if not _MODEL_SERIALIZER_MAP:
		_register_serializers()
	return _MODEL_SERIALIZER_MAP.get(model)

def serialize_obj_userfriendly(obj: Model) -> str | dict[str, Any]:
	"""Serialize a model object using its serializer or fall back to str()."""
	serializer_cls = get_registered_serializer(obj.__class__)
	if serializer_cls:
		return serializer_cls(obj).data
	if isinstance(obj, HssiModel):
		return obj.to_user_str()
	return str(obj)

class SerialView(enum.IntEnum):
	STANDARD = 1
	USER = 2
	JSONLD = 3

class HssiSerializer(ModelSerializer):
	"""Serializer for Software model data."""

	_view: SerialView = None
	default_view: SerialView = SerialView.STANDARD

	def view(self) -> SerialView:
		
		# parse serialview mode
		if self._view is None:
			req: Any | None = self.context.get("request")
			if not req:
				self._view = self.default_view
			else:
				params: QueryDict = req.query_params
				viewstr = params.get(Q_VIEW)
				if viewstr: 
					self._view = SerialView[viewstr.upper()]
				else: 
					self._view = self.default_view
		
		return self._view

	def to_representation_standard(self, instance: HssiModel):
		return super().to_representation(instance)
	
	def to_representation_user(self, instance: HssiModel):
		raise NotImplementedError
	
	def to_representation_jsonld(self, instance: HssiModel):
		raise NotImplementedError
	
	def to_internal_value_standard(self, data: dict[str: Any]):
		return super().to_internal_value(data)
	
	def to_internal_value_user(self, data: dict[str: Any]):
		raise NotImplementedError
	
	def to_internal_value_jsonld(self, data: dict[str: Any]):
		raise NotImplementedError

	def create_standard(self, validated_data: dict[str: Any]):
		return super().create(validated_data)

	def create_user(self, validated_data: dict[str: Any]):
		raise NotImplementedError

	def create_jsonld(self, validated_data: dict[str: Any]):
		raise NotImplementedError

	def update_standard(self, instance: HssiModel, validated_data: dict[str: Any]):
		return super().update(instance, validated_data)

	def update_user(self, instance: HssiModel, validated_data: dict[str: Any]):
		raise NotImplementedError

	def update_jsonld(self, instance: HssiModel, validated_data: dict[str: Any]):
		raise NotImplementedError

	def to_representation(self, instance: HssiModel):
		match self.view():
			case SerialView.STANDARD: return self.to_representation_standard(instance)
			case SerialView.USER: return self.to_representation_user(instance)
			case SerialView.JSONLD: return self.to_representation_jsonld(instance)
		raise NotImplementedError
	
	def to_internal_value(self, data: JsonSet):
		data = decamelize_data(data)
		match self.view():
			case SerialView.STANDARD: return self.to_internal_value_standard(data)
			case SerialView.USER: return self.to_internal_value_user(data)
			case SerialView.JSONLD: return self.to_internal_value_jsonld(data)
		raise NotImplementedError
	
	def create(self, validated_data: dict[str: Any]):
		match self.view():
			case SerialView.STANDARD: return self.create_standard(validated_data)
			case SerialView.USER: return self.create_user(validated_data)
			case SerialView.JSONLD: return self.create_jsonld(validated_data)
		raise NotImplementedError

	def update(self, instance: HssiModel, validated_data: dict[str: Any]):
		match self.view():
			case SerialView.STANDARD: return self.update_standard(instance, validated_data)
			case SerialView.USER: return self.update_user(instance, validated_data)
			case SerialView.JSONLD: return self.update_jsonld(instance, validated_data)
		raise NotImplementedError

	class Meta:
		abstract = True
