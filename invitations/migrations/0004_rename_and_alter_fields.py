from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('invitations', '0003_alter_eventtask_attendee'),
    ]

    operations = [
        migrations.RenameField(
            model_name='eventattendee',
            old_name='attendee',
            new_name='person',
        ),
        migrations.AlterField(
            model_name='event',
            name='occasion',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='event',
            name='location',
            field=models.CharField(max_length=500),
        ),
        migrations.AlterField(
            model_name='event',
            name='organizer',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to='invitations.person',
            ),
        ),
    ]
