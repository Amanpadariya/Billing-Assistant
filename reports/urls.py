from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("dashboard/", views.reports_dashboard, name="reports_dashboard"),
    path("export/csv/", views.export_report_csv, name="export_csv"),
    path("export/pdf/", views.export_report_pdf, name="export_pdf"),
]