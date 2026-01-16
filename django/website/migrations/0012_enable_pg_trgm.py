from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations


class Migration(migrations.Migration):

	dependencies = [
		("website", "0011_alter_cpuarchitecture_options_and_more"),
	]

	operations = [
		TrigramExtension(),
	]
