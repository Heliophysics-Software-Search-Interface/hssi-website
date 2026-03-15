""" Utility tools common for serializer submodules """

import enum
from typing import Any

from django.db.models import Model
from rest_framework import serializers

from ...models import HssiModel

class SerialFormat(enum.IntEnum):
	STANDARD = 1
	USER = 2
	JSONLD = 3

class HssiSerializer(serializers.ModelSerializer):
	"""Serializer for Software model data."""

	format: SerialFormat = SerialFormat.STANDARD

	def __init__(
		self, 
		instance: Model=None, 
		data: dict[str, Any]=..., 
		format: SerialFormat=..., 
		**kwargs
	):
		self.type = format or SerialFormat.STANDARD
		super().__init__(instance, data, **kwargs)

	def to_representation_standard(self, instance: HssiModel):
		return super().to_representation(instance)
	
	def to_representation_user(self, instance: HssiModel):
		raise NotImplementedError
	
	def to_representation_jsonld(self, instance: HssiModel):
		raise NotImplementedError
	
	def to_internal_value_standard(self, data: dict[str: Any]):
		return super().create(data)
	
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
		match self.format:
			case SerialFormat.STANDARD: return self.to_representation_standard(instance)
			case SerialFormat.USER: return self.to_representation_user(instance)
			case SerialFormat.JSONLD: return self.to_representation_jsonld(instance)
		raise NotImplementedError
	
	def to_internal_value(self, data: dict[str, Any]):
		match self.format:
			case SerialFormat.STANDARD: return self.to_internal_value_standard(data)
			case SerialFormat.USER: return self.to_internal_value_user(data)
			case SerialFormat.JSONLD: return self.to_internal_value_jsonld(data)
		raise NotImplementedError
	
	def create(self, validated_data: dict[str: Any]):
		match self.format:
			case SerialFormat.STANDARD: return self.create_standard(validated_data)
			case SerialFormat.USER: return self.create_user(validated_data)
			case SerialFormat.JSONLD: return self.create_jsonld(validated_data)
		raise NotImplementedError

	class Meta:
		abstract = True
