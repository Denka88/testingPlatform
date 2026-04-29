from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_user_patronymic'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='last_seen_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Последний заход в сеть'),
        ),
    ]
