from django.db import models

from .users import Users


class LoanData(models.Model):
    LOAN_TYPE_CHOICES = [
        ('CAR', 'Car'),
        ('HOM', 'Home'),
        ('EDU', 'Education'),
        ('PER', 'Personal')
    ]
    id = models.AutoField(primary_key=True, serialize=True)
    user_id = models.ForeignKey(Users, on_delete=models.PROTECT, null=True)
    loan_amount = models.IntegerField(null=False)
    loan_type = models.CharField(max_length=3, choices=LOAN_TYPE_CHOICES, null=False)
    interest = models.IntegerField(null=False)
    term_period = models.IntegerField(null=False)
    disbursement_date = models.DateTimeField(null=False)

    class Meta:
        db_table = 'loan_data'
        constraints = [
            models.UniqueConstraint(fields=['user_id', 'loan_type', 'loan_amount', 'disbursement_date'],
                                    name='UQ_user_id_loan_type_loan_amount_date')
        ]
