"""Custom DRF renderers for API responses."""

from typing import Any

from rest_framework.renderers import JSONRenderer


def _to_camel_case(value: str) -> str:
	"""Convert a snake_case string to camelCase."""
	parts = value.split("_")
	if not parts:
		return value
	head = parts[0]
	tail = "".join(word[:1].upper() + word[1:] for word in parts[1:] if word)
	return f"{head}{tail}"


def _camelize_data(data: Any) -> Any:
	"""Recursively convert dict keys from snake_case to camelCase."""
	if isinstance(data, dict):
		return {_to_camel_case(str(key)): _camelize_data(value) for key, value in data.items()}
	if isinstance(data, list):
		return [_camelize_data(item) for item in data]
	if isinstance(data, tuple):
		return tuple(_camelize_data(item) for item in data)
	return data


class CamelCaseJSONRenderer(JSONRenderer):
	"""JSON renderer that emits camelCase keys."""

	def render(self, data: Any, accepted_media_type: str | None = None, renderer_context: Any | None = None) -> bytes:
		if data is not None:
			data = _camelize_data(data)
		return super().render(data, accepted_media_type=accepted_media_type, renderer_context=renderer_context)
