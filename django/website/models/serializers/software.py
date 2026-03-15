"""Serializers for Software-related models."""

from ..software import Software
from .util import HssiSerializer

class SoftwareSerializer(HssiSerializer):
	"""Serializer for Software model data."""

	class Meta(HssiSerializer.Meta):
		model = Software
		fields = "__all__"
