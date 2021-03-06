# Generated by Django 3.0.2 on 2020-04-22 15:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('occasion', models.TextField()),
                ('date', models.DateTimeField()),
                ('location', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='EventAttendee',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('email', models.EmailField(max_length=254)),
            ],
        ),
        migrations.CreateModel(
            name='EventTask',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('task', models.CharField(max_length=255)),
                ('attendee', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='invitations.EventAttendee')),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='invitations.Event')),
            ],
        ),
        migrations.AddField(
            model_name='eventattendee',
            name='attendee',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='invitations.Person'),
        ),
        migrations.AddField(
            model_name='eventattendee',
            name='event',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='invitations.Event'),
        ),
        migrations.AddField(
            model_name='event',
            name='organizer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='invitations.Person'),
        ),
    ]
