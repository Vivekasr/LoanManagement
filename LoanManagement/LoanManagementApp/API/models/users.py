from django.db import models


class Users(models.Model):
    id = models.AutoField(primary_key=True, serialize=True)
    uuid = models.CharField(max_length=255, unique=True, null=False)
    name = models.CharField(max_length=255, null=False)
    email = models.CharField(max_length=255, null=False)
    annual_income = models.IntegerField(null=False)
    credit_score = models.IntegerField(null=False)

    class Meta:
        db_table = 'users'
        constraints = [
            models.UniqueConstraint(fields=['name', 'email'], name='UQ_name_email')
        ]
