import json
import datetime

from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view
from ..models.users import Users
from ..models.loan_data import LoanData
from ..models.emi_data import EmiData

LOAN_AMOUNT = {"CAR": 750000, "HOM": 8500000, "EDU": 5000000, "PER": 1000000}


@api_view(["POST"])
def apply_loan(request):
    event_body = request.data
    user_id = event_body.get("user_id")
    loan_type = event_body.get("loan_type")
    loan_amount = int(event_body.get("loan_amount"))
    interest_rate = int(event_body.get("interest_rate"))
    term_period = int(event_body.get("term_period"))
    disbursement_date = event_body.get("disbursement_date")

    if (
        user_id is None
        or loan_type is None
        or loan_amount is None
        or interest_rate is None
        or term_period is None
        or disbursement_date is None
    ):
        response = json.dumps({"message": "Please provide all necessary details!"})

        return HttpResponse(
            response,
            status=status.HTTP_400_BAD_REQUEST,
            content_type="application/json",
        )

    user_data = Users.objects.get(id=user_id)

    credit_score = user_data.credit_score
    annual_income = user_data.annual_income

    if credit_score < 450:
        response = json.dumps({"message": "Insufficient credit score!"})

        return HttpResponse(
            response,
            status=status.HTTP_406_NOT_ACCEPTABLE,
            content_type="application/json",
        )

    if annual_income < 150000:
        response = json.dumps({"message": "Insufficient Annual Income!"})

        return HttpResponse(
            response,
            status=status.HTTP_406_NOT_ACCEPTABLE,
            content_type="application/json",
        )

    if loan_amount > LOAN_AMOUNT[loan_type]:
        response = json.dumps({"message": "Loan amount exceeds loan limit!"})

        return HttpResponse(
            response,
            status=status.HTTP_406_NOT_ACCEPTABLE,
            content_type="application/json",
        )

    if interest_rate < 14:
        response = json.dumps({"message": "Interest rate too low!"})

        return HttpResponse(
            response,
            status=status.HTTP_406_NOT_ACCEPTABLE,
            content_type="application/json",
        )

    emi_map = create_loan_emi(
        user_id,
        loan_type,
        loan_amount,
        interest_rate,
        term_period,
        disbursement_date,
        annual_income,
    )

    if not emi_map["emi_success"]:
        response = json.dumps({"message": emi_map["message"]})

        return HttpResponse(
            response,
            status=status.HTTP_406_NOT_ACCEPTABLE,
            content_type="application/json",
        )

    loan_id = emi_map["emi"][0].loan_id.id
    date_1 = str(emi_map["emi"][0].date)

    due_dates = []

    for i in range(1, term_period):
        due_dates.append(str(emi_map["emi"][i].date))

    response = json.dumps(
        {
            "loan_id": loan_id,
            "due_dates": due_dates,
            "date": date_1,
            "amount_due": emi_map["total_amount"],
        }
    )

    return HttpResponse(
        response,
        status=status.HTTP_201_CREATED,
        content_type="application/json",
    )


def create_loan_emi(
    user_id,
    loan_type,
    loan_amount,
    interest_rate,
    term_period,
    disbursement_date,
    annual_income,
):
    monthly_income = annual_income / 12
    monthly_loan_amount = loan_amount / term_period
    monthly_interest = interest_rate * monthly_loan_amount / 100
    emi_list = []

    if monthly_interest * term_period <= 10000:
        return {
            "emi_success": False,
            "message": "EMI interest earned less than required limit!",
            "emi": emi_list,
        }

    if monthly_loan_amount + monthly_interest > 60 * monthly_income / 100:
        return {
            "emi_success": False,
            "message": "EMI amount exceeds monthly income limit!",
            "emi": emi_list,
        }

    if not LoanData.objects.filter(user_id=Users.objects.get(id=user_id)).exists():
        loan_data = LoanData(
            user_id=Users.objects.get(id=user_id),
            loan_amount=0,
            loan_type=loan_type,
            interest=interest_rate,
            term_period=term_period,
            disbursement_date=datetime.datetime.strptime(disbursement_date, "%Y-%m-%d"),
        )

        loan_data.save()

    date = datetime.datetime.strptime(disbursement_date, "%Y-%m-%d")

    total_emi = 0

    while term_period > 0:
        year = date.year
        if date.month == 12:
            year += 1
        month = date.month % 12 + 1
        emi_amount = monthly_loan_amount + monthly_interest

        if EmiData.objects.filter(
            loan_id=LoanData.objects.get(user_id=user_id),
            emi_amount=emi_amount,
            date=datetime.date(year, month, 1),
        ).exists():
            return {
                "emi_success": False,
                "message": "Loan is already processed!",
                "emi": emi_list,
            }

        emi_details = EmiData(
            loan_id=LoanData.objects.get(user_id=user_id),
            emi_amount=emi_amount,
            amount_paid=0,
            date=datetime.date(year, month, 1),
            is_paid=False,
        )
        emi_details.save()
        term_period -= 1
        date = datetime.date(year, month, 1)
        emi_list.append(emi_details)
        total_emi += emi_amount

    LoanData.objects.filter(user_id=Users.objects.get(id=user_id)).update(loan_amount=total_emi)

    return {"emi_success": True, "total_amount": total_emi, "emi": emi_list}
