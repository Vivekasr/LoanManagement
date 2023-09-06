import csv
import json

from django.http import HttpResponse
from rest_framework import status
from django.contrib.staticfiles import finders
from rest_framework.decorators import api_view
from ..models.users import Users


@api_view(["POST"])
def register_user(request):
    event_body = request.data
    aadhar_id = event_body.get("aadhar_id")
    name = event_body.get("name")
    email_id = event_body.get("email_id")
    annual_income = event_body.get("annual_income")

    if aadhar_id is None or name is None or email_id is None or annual_income is None:
        response = json.dumps({"message": "Please provide all necessary details!"})

        return HttpResponse(
            response,
            status=status.HTTP_400_BAD_REQUEST,
            content_type="application/json",
        )

    credit_score = get_credit_score(aadhar_id)

    try:
        Users.objects.update_or_create(
            name=name,
            uuid=aadhar_id,
            email=email_id,
            defaults={
                'annual_income':annual_income,
                'credit_score':credit_score,
            }
        )
    except Exception as ex:
        response = json.dumps({"message": "Cannot save the data"})

        return HttpResponse(
            response, status=status.HTTP_409_CONFLICT, content_type="application/json"
        )

    new_user_id = Users.objects.filter(name=name, email=email_id).values_list("id")[0][0]

    response = json.dumps({"user_id": new_user_id})

    return HttpResponse(
        response, status=status.HTTP_201_CREATED, content_type="application/json"
    )


def get_credit_score(aadhar_id):
    csv_file_path = finders.find("transactions_data Backend.csv")
    transaction_amount = 0

    transaction_map = {}

    with open(csv_file_path, "r") as file:
        csv_data = csv.DictReader(file)
        for row in csv_data:
            aadhar_id_csv = row["user"]
            if aadhar_id_csv == aadhar_id:
                transaction_type = row["transaction_type"]
                amount = int(row["amount"])
                if transaction_type == "DEBIT":
                    transaction_amount -= amount
                else:
                    transaction_amount += amount

    if transaction_amount < 100000:
        return 300

    if transaction_amount > 1000000:
        return 900

    return (((transaction_amount - 100000) // 15000) * 10) + 300
