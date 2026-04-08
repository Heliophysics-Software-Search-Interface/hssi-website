
from .util import HssiSerializer
from ..people import Person

class PersonSerializer(HssiSerializer):

	class Meta(HssiSerializer.Meta):
		model = Person
		fields = "__all__"
