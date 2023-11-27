# Generated by Django 4.2.1 on 2023-06-18 01:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChatHistoryModel',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('userid', models.CharField(max_length=100)),
                ('functionid', models.CharField(max_length=100)),
                ('content', models.CharField(max_length=20000)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.DeleteModel(
            name='HistoryModel',
        ),
    ]