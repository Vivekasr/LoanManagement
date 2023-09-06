from django.db import models

from .loan_data import LoanData


class EmiData(models.Model):
    id = models.AutoField(primary_key=True, serialize=True)
    loan_id = models.ForeignKey(LoanData, on_delete=models.PROTECT, null=True)
    emi_amount = models.IntegerField(null=False)
    amount_paid = models.IntegerField(null=False)
    date = models.DateTimeField(null=False)
    is_paid = models.BooleanField(null=False)

    class Meta:
        db_table = 'emi_data'
        constraints = [
            models.UniqueConstraint(fields=['loan_id', 'date', 'emi_amount'], name='UQ_loan_id_date_emi_amount')
        ]
