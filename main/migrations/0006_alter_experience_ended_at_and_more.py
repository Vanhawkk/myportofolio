import datetime

from django.conf import settings
from django.db import migrations, models
from django.utils import timezone


def copy_experience_dates(apps, schema_editor):
    Experience = apps.get_model("main", "Experience")

    for experience in Experience.objects.all().iterator():
        experience.started_on = (
            experience.started_at.date()
            if experience.started_at
            else timezone.localdate()
        )
        experience.ended_on = (
            experience.ended_at.date()
            if experience.ended_at
            else None
        )
        experience.save(update_fields=["started_on", "ended_on"])


def restore_experience_datetimes(apps, schema_editor):
    Experience = apps.get_model("main", "Experience")

    for experience in Experience.objects.all().iterator():
        started_at = datetime.datetime.combine(
            experience.started_on,
            datetime.time.min,
        )
        ended_at = (
            datetime.datetime.combine(
                experience.ended_on,
                datetime.time.min,
            )
            if experience.ended_on
            else None
        )

        if settings.USE_TZ:
            started_at = timezone.make_aware(started_at)
            if ended_at:
                ended_at = timezone.make_aware(ended_at)

        experience.started_at = started_at
        experience.ended_at = ended_at
        experience.save(update_fields=["started_at", "ended_at"])


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_experience_starred_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='experience',
            name='started_on',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='experience',
            name='ended_on',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.RunPython(
            copy_experience_dates,
            restore_experience_datetimes,
        ),
        migrations.RemoveField(
            model_name='experience',
            name='started_at',
        ),
        migrations.RemoveField(
            model_name='experience',
            name='ended_at',
        ),
        migrations.RenameField(
            model_name='experience',
            old_name='started_on',
            new_name='started_at',
        ),
        migrations.RenameField(
            model_name='experience',
            old_name='ended_on',
            new_name='ended_at',
        ),
        migrations.AlterField(
            model_name='experience',
            name='started_at',
            field=models.DateField(default=timezone.localdate),
        ),
    ]
