from django.urls import path
from .views.register_user import register_user
from .views.apply_loan import apply_loan
from .views.make_payment import make_payment
from .views.get_statement import get_statement

urlpatterns = [
    path('register-user/', register_user, name='register-user'),
    path('apply-loan/', apply_loan, name='apply-loan'),
    path('make-payment/', make_payment, name='make-payment'),
    path('get-statement/', get_statement, name='get-statement'),
]
