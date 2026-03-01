import uuid, typing
import django.db.models.deletion
from django.db import migrations, models
from django.apps.registry import Apps
from django.db.backends.base.schema import BaseDatabaseSchemaEditor

if typing.TYPE_CHECKING:
    from ..models.software import Software
    from ..models.submission_info import SubmissionInfo

submission_software_map: dict[uuid.UUID, uuid.UUID]

def create_submission_software_map(apps: Apps, schema_editor: BaseDatabaseSchemaEditor):
    global submission_software_map
    submission_software_map = {}
    software_model: type[Software] = apps.get_model("website", "Software")

    for software in software_model.objects.all():
        if not software.submissionInfo: 
            continue
        # at this point in the migration, software.submissionInfo still exists as a OneToOne field
        submission_uid = software.submissionInfo.id
        software_uid = software.id
        submission_software_map[submission_uid] = software_uid

def apply_submission_software_map(apps: Apps, scema_editor: BaseDatabaseSchemaEditor):
    global submission_software_map
    software_model: type[Software] = apps.get_model("website", "Software")
    submission_info_model: type[SubmissionInfo] = apps.get_model("website", "SubmissionInfo")

    for submission_uid, software_uid in submission_software_map.items():
        submission = submission_info_model.objects.get(id=submission_uid)
        submission.software = software_model.objects.get(id=software_uid)
        submission.save()

    del submission_software_map

class Migration(migrations.Migration):

    dependencies = [
        ('website', '0012_alter_software_logo_delete_image'),
    ]

    operations = [
        migrations.RunPython(create_submission_software_map),
        migrations.RemoveField(
            model_name='software',
            name='submissionInfo',
        ),
        migrations.AddField(
            model_name='submissioninfo',
            name='software',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='submission_info', to='website.software'),
        ),
        migrations.RunPython(apply_submission_software_map)
    ]
