import uuid, re

from django.contrib.auth.models import AbstractUser, AnonymousUser
from django.db.models import Model, Manager
from django.db.models.fields import Field
from enum import IntEnum

SPACE_REPLACE = re.compile(r'[_\-.]')

class RequirementLevel(IntEnum):
	OPTIONAL = 0
	RECOMMENDED = 1
	MANDATORY = 2

	def __str__(self) -> str: return str(self.value)

class AccessLevel(IntEnum):
	PUBLIC = 0
	SUBMITTER = 1
	CURATOR = 2
	STAFF = 3
	ADMIN = 4

	@classmethod
	def from_user(cls, user: AbstractUser | AnonymousUser) -> 'AccessLevel':
		access = cls.PUBLIC
		if user.is_superuser:
			access = cls.ADMIN
		elif user.is_staff:
			access = cls.STAFF
		elif user.is_authenticated:
			access = cls.SUBMITTER
		return access

REQ_LVL_ATTR = "data-hssi-required"

def find_database_references(object: Model) -> list[tuple[Model, Field]]:
	"""
	get all (related object, field) pairs on all objects in the database that 
	reference the specified object
	"""
	refs = []
	for field in object._meta.get_fields():
		if field.is_relation and field.auto_created and not field.concrete:
			rel_name = field.get_accessor_name()
			related: Manager = getattr(object, rel_name)
			for rel in related.all():
				refs.append((rel, field.field))
	return refs