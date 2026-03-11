from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('invitations', '0002_alter_event_id_alter_eventattendee_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eventtask',
            name='attendee',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='invitations.eventattendee',
            ),
        ),
    ]
