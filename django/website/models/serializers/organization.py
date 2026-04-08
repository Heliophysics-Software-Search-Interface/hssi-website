
from .util import HssiSerializer
from ..organizations import Organization

class OrganizationSerializer(HssiSerializer):

	class Meta(HssiSerializer.Meta):
		model = Organization
		fields = "__all__"
