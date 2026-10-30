from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0008_remove_userprofile_preferred_language'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='preferred_language',
            field=models.CharField(choices=[('th', 'ไทย'), ('en', 'English')], default='th', max_length=10),
            preserve_default=False,
        ),
    ]
