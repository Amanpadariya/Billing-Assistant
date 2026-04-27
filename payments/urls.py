from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path("add/<uuid:bill_id>/", views.add_payment, name="add_payment"),
    path("bill/<uuid:bill_id>/", views.bill_payments, name="bill_payments"),
    path("delete/<int:payment_id>/", views.delete_payment, name="delete_payment"),
]