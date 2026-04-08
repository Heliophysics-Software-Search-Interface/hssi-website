
from .util import HssiSerializer
from ..software import Submitter

class SubmitterSerializer(HssiSerializer):

	class Meta(HssiSerializer.Meta):
		model = Submitter
		fields = "__all__"
		depth = 1
