import json
import datetime

from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view
from ..models.loan_data import LoanData
from ..models.emi_data import EmiData


@api_view(['GET'])
def get_statement(request):
    event_body = request.data
    loan_id = event_body.get("loan_id")

    if loan_id is None:
        response = json.dumps({"message": "Please provide all necessary details!"})

        return HttpResponse(
            response,
            status=status.HTTP_400_BAD_REQUEST,
            content_type="application/json",
        )

    if not LoanData.objects.filter(id=loan_id).exists():
        response = json.dumps({"message": "Loan id does not exists!"})

        return HttpResponse(
            response,
            status=status.HTTP_400_BAD_REQUEST,
            content_type="application/json",
        )

    today_date = str(datetime.datetime.now())

    loan_data = LoanData.objects.get(id=loan_id)

    principal_amount = loan_data.loan_amount
    interest = loan_data.interest

    amount_paid = sum(EmiData.objects.filter(loan_id=loan_id, is_paid=True).values_list('amount_paid', flat=True))
    amount_left = sum(EmiData.objects.filter(loan_id=loan_id, is_paid=False).values_list('emi_amount', flat=True))

    left_emi_details = EmiData.objects.filter(loan_id=loan_id, is_paid=False).values('emi_amount', 'date')
    left_emi_details_list = [[data['emi_amount'], str(data['date'])] for data in left_emi_details]
    latest_emi_date = str(left_emi_details[0]['date'])

    response = json.dumps({
        'Date':today_date,
        'Principal':principal_amount,
        'Interest':interest,
        'Amount Paid':amount_paid,
        'Amount Left':amount_left,
        'Upcoming Transactions':left_emi_details_list,
        'Date EMI':latest_emi_date
    })

    return HttpResponse(
        response,
        status=status.HTTP_200_OK,
        content_type="application/json",
    )
