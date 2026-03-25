import uuid

from django.test import SimpleTestCase

from .models import DataInput, FunctionCategory, ProgrammingLanguage, Region
from .util import build_software_filter_query, shorten_software_filter_value

FILTER_CASES = [
	("data_sources",           DataInput,            "a1f8de3a-1bde-4995-94e5-e88e841a62a6", "ofjeOhvds"),
	("related_region",         Region,               "b450b02c-ac3e-466e-b3a1-70040b169562", "tFCwLKwr"),
	("programming_language",   ProgrammingLanguage,  "1b6ddaa6-6885-46b3-b59a-ea119e61bd74", "G23apmip"),
	("software_functionality", FunctionCategory,     "332b6567-bdd1-4132-a0c5-532e78b5538c", "MytlZ73f"),
]


class SoftwareFilterEncodingTests(SimpleTestCase):
	def test_tokens_match_frontend_encoding(self):
		for field, _, uid_str, expected_token in FILTER_CASES:
			with self.subTest(field=field):
				self.assertEqual(
					shorten_software_filter_value(field, uuid.UUID(uid_str)),
					expected_token,
				)

	def test_homepage_filter_urls(self):
		for field, model_cls, uid_str, _ in FILTER_CASES:
			with self.subTest(model=model_cls.__name__):
				obj = model_cls(id=uuid.UUID(uid_str), name="test")
				self.assertEqual(
					obj.get_homepage_filter_url(),
					f"/?{build_software_filter_query(field, obj.id)}",
				)
