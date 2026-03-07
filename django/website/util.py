import re, typing

from django.contrib.auth.models import AbstractUser, AnonymousUser
from django.db.models import Model, Manager, ManyToManyField
from django.db import transaction
from django.db.models.fields import Field
from sortedm2m.fields import SortedManyToManyField
from enum import IntEnum

if typing.TYPE_CHECKING:
	from django.db.models.manager import ManyToManyRelatedManager

SPACE_REPLACE = re.compile(r'[_\-.]')
PARENTHESIS_MATCH = re.compile(r"\(([^)]*)\)")

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

def name_to_abbreviation(name: str) -> str:
	splname = name.replace('-', ' ').split()
	match len(splname):
		case 0: return "????"
		case 1: return name[0:4].title()
		case 2: return splname[0][0:2].title() + splname[1][0:2].title()
		case 3: return (
			splname[0][0:2].title() + 
			splname[1][0].upper() + 
			splname[2][0].upper()
		)
		case _: return (
			splname[0][0].upper() + 
			splname[1][0].upper() + 
			splname[-2][0].upper() + 
			splname[-1][0].upper()
		)
	return name

def find_database_references(object: Model) -> list[tuple[Model, Field]]:
	"""
	get all (related object, field) pairs on all objects in the database that 
	reference the specified object
	"""
	refs = []
	for field in object._meta.get_fields():
		if field.is_relation and field.auto_created and not field.concrete:
			rel_name = field.get_accessor_name()
			try:
				related: Manager = getattr(object, rel_name)
				for rel in related.all():
					refs.append((rel, field.field))
			except Exception as e:
				print(f"could not resolve '{rel_name}' on {str(object)} |", e)
	return refs

@transaction.atomic
def replace_database_references(old_object: Model, new_object: Model, unique_mapping: bool = True):

	oldrefs = find_database_references(old_object)
	print(f"replacing {len(oldrefs)} '{old_object}' references..")
	
	for refobj, field in oldrefs:
		if isinstance(field, ManyToManyField):
			# if it's a sorted m2m field, the sort_value must be 
			# preserved so we modify the through table directly
			if isinstance(field, SortedManyToManyField):
				sm2m_field: SortedManyToManyField = field
				through: type[Model] = (
					sm2m_field.through 
					if hasattr(sm2m_field, "through") else 
					sm2m_field.remote_field.through
				)
				old_obj_field: str = old_object._meta.model_name.lower()
				old_kwargs = {
					refobj._meta.model_name.lower(): refobj.pk,
					old_obj_field: old_object.pk
				}
				new_kwargs = {
					refobj._meta.model_name.lower(): refobj.pk,
					old_obj_field: new_object.pk
				}

				# if we have a mapping to non-unique values, we can have fields 
				# that are mapped to the same new_object twice
				if not unique_mapping:
					if not through.objects.filter(**new_kwargs).exists():
						entry = through.objects.get(**old_kwargs)
						setattr(entry, old_obj_field, new_object)
						entry.save()

					# if the newly mapped object already exists, we just 
					# delete the old reference
					else:
						entry = through.objects.get(**old_kwargs).delete()

				# if we are forcing the mapping to unique values, we don't 
				# check to see if the new object is already referenced because 
				# we want it to throw an error if thats the case
				else:
					entry = through.objects.get(**old_kwargs)
					setattr(entry, old_obj_field, new_object)
					entry.save()
			else:
				m2m_field: ManyToManyRelatedManager = getattr(refobj, field.name)
				m2m_field.remove(old_object)

				# if the mapping is not gaurenteed to be unique, we need to 
				# make sure the new object is not already referenced
				if unique_mapping or not m2m_field.contains(new_object):
					m2m_field.add(new_object)
				
		else: setattr(refobj, field.name, new_object)
		print(f"updated field '{refobj}->{field.name}'")