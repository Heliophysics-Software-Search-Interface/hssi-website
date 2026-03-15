""" Utility tools common for serializer submodules """

import enum
from typing import Any

from django.http.request import QueryDict
from django.db.models import Model
from rest_framework import serializers

from hssi.camel_case_renderer import JsonSet, decamelize_data
from ...models import HssiModel

QPARAM_VIEW: str = "view"

class SerialView(enum.IntEnum):
	STANDARD = 1
	USER = 2
	JSONLD = 3

class HssiSerializer(serializers.ModelSerializer):
	"""Serializer for Software model data."""

	_view: SerialView = None

	def view(self) -> SerialView:
		
		# parse serialview mode
		if self._view is None:
			params: QueryDict = self.context["request"].query_params
			viewstr = params.get(QPARAM_VIEW)
			if viewstr: 
				self._view = SerialView[viewstr.upper()]
			else: 
				self._view = SerialView.STANDARD
		
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

	class Meta:
		abstract = True
