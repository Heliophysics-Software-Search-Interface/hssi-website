from django.db import migrations, models


class Migration(migrations.Migration):

	dependencies = [
		('website', '0019_instrumentobservatory_landing_url'),
	]

	operations = [
		migrations.AddField(
			model_name='software',
			name='date_modified',
			field=models.DateTimeField(blank=True, editable=False, null=True),
		),
	]
