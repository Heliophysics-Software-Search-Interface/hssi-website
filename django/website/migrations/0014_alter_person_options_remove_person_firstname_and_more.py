import uuid, typing
from django.db import migrations, models
from django.apps.registry import Apps
from django.db.backends.base.schema import BaseDatabaseSchemaEditor

if typing.TYPE_CHECKING:
    from ..models.people import Person

class Migration(migrations.Migration):

    dependencies = [
        ('website', '0013_remove_software_submissioninfo_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='person',
            options={'ordering': ['family_name', 'given_name'], 'verbose_name_plural': 'People'},
        ),
        migrations.RenameField(
            model_name='person',
            old_name='firstName',
            new_name='given_name',
        ),
        migrations.RenameField(
            model_name='person',
            old_name='lastName',
            new_name='family_name',
        ),
        migrations.RemoveField(
            model_name='relateditem',
            name='authors',
        ),
        migrations.RemoveField(
            model_name='relateditem',
            name='creditText',
        ),
        migrations.RemoveField(
            model_name='relateditem',
            name='license',
        ),
    ]
