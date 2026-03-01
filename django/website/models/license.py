""" Container module for Licence model and related information. """

from django.db import models
from django.db.models import Q

from ..util import *
from .base import LEN_NAME, HssiModel

class License(HssiModel):
	access = AccessLevel.PUBLIC
	name = models.CharField(max_length=LEN_NAME)
	url = models.URLField(blank=True, null=True)

	@classmethod
	def get_top_field(cls): return cls._meta.get_field("name")

	@classmethod
	def get_other_licence(cls): 
		"""return the primary 'Other' licence, the one with no URL"""
		return cls.objects.filter(name="Other").filter(
			Q(url="") | Q(url__isnull=True)
		).first()

	def get_search_terms(self):
		terms = super().get_search_terms()
		if self.url:
			terms.append(self.url)
		return terms
	
	class Meta: ordering = ['name']
	def __str__(self): return self.name