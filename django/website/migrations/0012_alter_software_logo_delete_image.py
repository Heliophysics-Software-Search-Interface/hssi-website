import uuid, typing
from django.db import migrations, models
from django.apps.registry import Apps
from django.db.backends.base.schema import BaseDatabaseSchemaEditor

if typing.TYPE_CHECKING:
	from ..models import Software

logo_url_map: dict[uuid.UUID, str] = {}

def create_logo_url_map(apps: Apps, schema_editor: BaseDatabaseSchemaEditor):
	global logo_url_map
	software_model: type[Software] = apps.get_model("website", "Software")
	for software in software_model.objects.all():
		if software.logo:
			logo_url = software.logo.url
			logo_url_map[software.id] = logo_url

def apply_logo_url_map(apps: Apps, schema_editor: BaseDatabaseSchemaEditor):
	global logo_url_map
	software_model: type[Software] = apps.get_model("website", "Software")
	for uid, logo_url in logo_url_map.items():
		entry = software_model.objects.get(id=uid)
		entry.logo = logo_url
		entry.save()
	del logo_url_map

class Migration(migrations.Migration):

	dependencies = [
		('website', '0011_remove_category_children_remove_resource_categories_and_more'),
	]

	operations = [
		migrations.RunPython(create_logo_url_map),
		migrations.AlterField(
			model_name='software',
			name='logo',
			field=models.URLField(blank=True, null=True),
		),
		migrations.RunPython(apply_logo_url_map),
		migrations.DeleteModel(
			name='Image',
		),
	]
