import json
import datetime

from django.http import HttpResponse
from django.db.models import Count
from rest_framework import status
from rest_framework.decorators import api_view
from ..models.loan_data import LoanData
from ..models.emi_data import EmiData


@api_view(["POST"])
def make_payment(request):
    event_body = request.data
    loan_id = event_body.get("loan_id")
    amount = int(event_body.get("amount"))

    if loan_id is None or amount is None:
        response = json.dumps({"message": "Please provide all necessary details!"})

        return HttpResponse(
            response,
            status=status.HTTP_400_BAD_REQUEST,
            content_type="application/json",
        )

    total_emi_left = EmiData.objects.filter(loan_id=loan_id, is_paid=False).order_by(
        "date"
    )
    total_emi_left_count = len(total_emi_left)
    latest_emi = total_emi_left[0]

    latest_emi_date = latest_emi.date
    latest_emi_month = latest_emi_date.month
    latest_emi_year = latest_emi_date.year

    datetime_now = datetime.date(2024, 7, 1)
    month_now = datetime_now.month
    year_now = datetime_now.year

    if (latest_emi_month > month_now) or (
        latest_emi_year > year_now and latest_emi_month < month_now
    ):
        response = json.dumps({"message": "Payment already paid for the month!"})

        return HttpResponse(
            response,
            status=status.HTTP_406_NOT_ACCEPTABLE,
            content_type="application/json",
        )

    if (latest_emi_month < month_now) or (latest_emi_year < year_now):
        response = json.dumps(
            {"message": "Delayed payment. Contact your nearest bank branch!"}
        )

        return HttpResponse(
            response,
            status=status.HTTP_406_NOT_ACCEPTABLE,
            content_type="application/json",
        )

    latest_emi_amount = latest_emi.emi_amount

    if amount == latest_emi_amount:
        EmiData.objects.filter(
            loan_id=loan_id, is_paid=False, date=latest_emi_date
        ).update(is_paid=True, amount_paid=amount)

        response = json.dumps({"message": "Payment successfully paid for the month!"})

        return HttpResponse(
            response,
            status=status.HTTP_200_OK,
            content_type="application/json",
        )

    if amount < latest_emi_amount:
        balance = latest_emi_amount - amount
        interest = LoanData.objects.get(id=loan_id).interest

        new_emi_amount = (
            latest_emi_amount + (balance * interest / 100) / total_emi_left_count
        )
        EmiData.objects.filter(
            loan_id=loan_id, is_paid=False, date=latest_emi_date
        ).update(is_paid=True, amount_paid=amount)
        EmiData.objects.filter(loan_id=loan_id, is_paid=False).update(
            emi_amount=new_emi_amount
        )
        new_loan_amount = sum(EmiData.objects.filter(loan_id=loan_id).values_list('emi_amount', flat=True))
        LoanData.objects.filter(id=loan_id).update(loan_amount=new_loan_amount)

        response = json.dumps(
            {
                "message": "Partial-Payment successfully paid for the month! Added new emi amount to left payments"
            }
        )

        return HttpResponse(
            response,
            status=status.HTTP_200_OK,
            content_type="application/json",
        )
