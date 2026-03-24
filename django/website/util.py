import uuid, re

from django.contrib.auth.models import AbstractUser, AnonymousUser
from django.db.models import Model, Manager
from django.db.models.fields import Field
from django.db.transaction import atomic
from enum import IntEnum

from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from django.db.models.manager import RelatedManager

SPACE_REPLACE = re.compile(r'[_\-.]')
SOFTWARE_FUNCAT_FILEPATH = "./software_funcat_map.csv"

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
	return

def export_software_functioncategory_names() -> str:
	from .models import Software, FunctionCategory

	# find the appropriate field name for different versions of this codebase
	names = ["softwareName", "software_name"]
	software_fieldname: str = ""
	for field in Software._meta.get_fields():
		if field.name in names:
			software_fieldname = field.name
			break
	
	names = ["softwareFunctionality", "software_functionality"]
	category_fieldname: str = ""
	for field in Software._meta.get_fields():
		if field.name in names:
			category_fieldname = field.name
			break

	software_funcat_map: dict[str, set[str]] = {}
	for software in Software.objects.all():
		name = getattr(software, software_fieldname)
		funcats: RelatedManager[FunctionCategory] = getattr(software, category_fieldname)
		if not name in software_funcat_map:
			software_funcat_map[name] = set()
		for funcat in funcats.all():
			software_funcat_map[name].add(funcat.get_name_path().replace("->", ": "))
	
	output: str = ""
	for software_name, funcat_fullnames in software_funcat_map.items():
		namelist = ""
		for funcat_fullname in funcat_fullnames:
			namelist += f"{funcat_fullname},"
		output += f"{software_name}={namelist[:-1]}\n"

	with open(SOFTWARE_FUNCAT_FILEPATH, 'w') as file:
		file.write(output)
	return output

@atomic
def import_software_functioncategory_names(data: str = None):
	from .models import Software, FunctionCategory

	if data is None:
		with open(SOFTWARE_FUNCAT_FILEPATH, 'r') as file:
			data = file.read()
		
	# find the appropriate field name for different versions of this codebase
	names = ["softwareName", "software_name"]
	software_fieldname: str = ""
	for field in Software._meta.get_fields():
		if field.name in names:
			software_fieldname = field.name
			break
	
	names = ["softwareFunctionality", "software_functionality"]
	category_fieldname: str = ""
	for field in Software._meta.get_fields():
		if field.name in names:
			category_fieldname = field.name
			break
	
	lines = data.splitlines()
	for line in lines:
		software_name, line_data = line.split("=")
		funcat_names = line_data.split(",")

		kwargs = { software_fieldname: software_name }
		software = Software.objects.get(**kwargs)

		funcats: list[FunctionCategory] = []
		for funcat_name in funcat_names:
			# TODO get function category by full name path
			pass

		for funcat in funcats:
			field: RelatedManager[FunctionCategory] = getattr(software, category_fieldname)
			field.add(funcat)
		
		software.save()
		
