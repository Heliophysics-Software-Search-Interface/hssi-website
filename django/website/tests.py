import uuid

from django.test import SimpleTestCase

from .models import FunctionCategory, ProgrammingLanguage
from .util import build_software_filter_query, shorten_software_filter_value


class SoftwareFilterEncodingTests(SimpleTestCase):
	def test_programming_language_token_matches_frontend_encoding(self):
		language_id = uuid.UUID("1b6ddaa6-6885-46b3-b59a-ea119e61bd74")
		self.assertEqual(
			shorten_software_filter_value("programming_language", language_id),
			"G23apmip",
		)

	def test_programming_language_homepage_filter_url(self):
		language = ProgrammingLanguage(
			id=uuid.UUID("1b6ddaa6-6885-46b3-b59a-ea119e61bd74"),
			name="Python 3.x",
		)
		self.assertEqual(
			language.get_homepage_filter_url(),
			f"/?{build_software_filter_query('programming_language', language.id)}",
		)

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
