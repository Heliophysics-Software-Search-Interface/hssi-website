from django.contrib.auth.models import AbstractUser, AnonymousUser
from enum import IntEnum

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