import uuid

from django.test import SimpleTestCase

from .models import FunctionCategory
from .util import build_software_filter_query, shorten_software_filter_value


class SoftwareFilterEncodingTests(SimpleTestCase):
	def test_software_functionality_token_matches_frontend_encoding(self):
		func_id = uuid.UUID("332b6567-bdd1-4132-a0c5-532e78b5538c")
		self.assertEqual(
			shorten_software_filter_value("software_functionality", func_id),
			"MytlZ73f",
		)

	def test_function_category_homepage_filter_url(self):
		func = FunctionCategory(
			id=uuid.UUID("332b6567-bdd1-4132-a0c5-532e78b5538c"),
			name="Coordinate Transforms",
		)
		self.assertEqual(
			func.get_homepage_filter_url(),
			f"/?{build_software_filter_query('software_functionality', func.id)}",
		)
