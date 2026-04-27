from django.urls import path
from . import views

app_name = "billing"

urlpatterns = [

    # ---------------- PUBLIC ----------------
    

    # View invoice
    path('invoice/<str:invoice_number>/', views.invoice_detail, name='invoice_detail'),
    # Customer history
    path("customer/<str:phone>/", views.customer_history, name="customer_history"),


   
]