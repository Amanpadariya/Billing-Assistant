from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

app_name = "staffpanel"

urlpatterns = [

    # ---------------- DASHBOARD ----------------
    path("dashboard/", views.dashboard, name="dashboard"),


    # ---------------- BILLING ----------------
    path("create-bill/", views.create_bill, name="create_bill"),
    path("bills/", views.bill_list, name="bill_list"),
    path("bills/toggle-status/<uuid:pk>/", views.toggle_bill_status, name="toggle_bill_status"),
    path("bills/cancel/<uuid:pk>/", views.cancel_bill, name="cancel_bill"),
    path("bills/delete/<uuid:pk>/", views.delete_bill, name="delete_bill"),


    path("bill-search/", views.bill_search_suggestions, name="bill_search"),

 

    # ---------------- INVOICE ----------------
    path("invoice/<str:invoice_number>/pdf/", views.invoice_pdf, name="invoice_pdf"),
  


    path("customer-search/", views.customer_search, name="customer_search"),
    path('logout/', LogoutView.as_view(), name='logout'),
]