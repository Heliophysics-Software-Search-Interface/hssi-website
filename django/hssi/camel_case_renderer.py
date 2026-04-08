"""Custom DRF camel case renderer for API responses."""

from __future__ import annotations

import re
from typing import Any, TypeAlias

from rest_framework.renderers import JSONRenderer


JsonValue: TypeAlias = str | int | float | bool | None
JsonSet: TypeAlias = (
	JsonValue | 
	dict[str, "JsonValue"] | 
	list["JsonValue"] | 
	tuple["JsonValue", ...]
)

CAMEL_TO_SNAKE_RE_1 = re.compile(r"(.)([A-Z][a-z]+)")
CAMEL_TO_SNAKE_RE_2 = re.compile(r"([a-z0-9])([A-Z])")

def to_camel_case(value: str) -> str:
	"""Convert a snake_case string to camelCase."""
	parts = value.split("_")
	if not parts:
		return value
	head = parts[0]
	tail = "".join(word[:1].upper() + word[1:] for word in parts[1:] if word)
	return f"{head}{tail}"

def camel_to_snake(name: str) -> str:
	"""Convert a camelCase string to snake_case."""
	s1 = CAMEL_TO_SNAKE_RE_1.sub(r"\1_\2", name)
	return CAMEL_TO_SNAKE_RE_2.sub(r"\1_\2", s1).lower()

def camelize_data(data: JsonSet) -> JsonSet:
	"""Recursively convert dict keys from snake_case to camelCase."""
	if isinstance(data, dict):
		return {to_camel_case(str(key)): camelize_data(value) for key, value in data.items()}
	if isinstance(data, list):
		return [camelize_data(item) for item in data]
	if isinstance(data, tuple):
		return tuple(camelize_data(item) for item in data)
	return data

def decamelize_data(data: JsonSet) -> JsonSet:
	"""Recursively convert dict keys from camelCase to snake_case."""
	if isinstance(data, dict):
		return {camel_to_snake(str(key)): decamelize_data(value) for key, value in data.items()}
	if isinstance(data, list):
		return [decamelize_data(item) for item in data]
	if isinstance(data, tuple):
		return tuple(decamelize_data(item) for item in data)
	return data


class CamelCaseJSONRenderer(JSONRenderer):
	"""JSON renderer that emits camelCase keys."""

	def render(
		self, 
		data: Any, accepted_media_type: str | None = None, 
		renderer_context: Any | None = None
	) -> bytes:
		if data is not None:
			data = camelize_data(data)
		return super().render(
			data, 
			accepted_media_type=accepted_media_type, 
			renderer_context=renderer_context
		)
