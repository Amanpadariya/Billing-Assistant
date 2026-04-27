from django.shortcuts import render
from billing.models import Bill, BillItem
from django.utils.timezone import now
from datetime import datetime, timedelta,time
from django.db.models import Sum
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
import csv
from account.utils import role_required
from payments.models import Payment





@role_required(["ADMIN","STAFF"])
def reports_dashboard(request):

    today = now().date()

    range_filter = request.GET.get("range")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    # ---------------- DATE FILTER ----------------
    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        except:
            start_date = today - timedelta(days=6)
            end_date = today

    elif range_filter == "today":
        start_date = today
        end_date = today

    elif range_filter == "month":
        start_date = today.replace(day=1)
        end_date = today

    else:
        start_date = today - timedelta(days=6)
        end_date = today

    # ---------------- BILLS ----------------
    all_bills = Bill.objects.filter(
        created_at__date__range=[start_date, end_date]
    ).prefetch_related("payments")

    paid_bills_qs = all_bills.filter(payment_status="PAID")

    # ---------------- SUMMARY ----------------
    total_bills = all_bills.count()
    paid_bills = paid_bills_qs.count()
    cancelled_bills = all_bills.filter(payment_status="CANCELLED").count()

    # 🔥 TOTAL SALES (based on bill)
    total_sales = sum(b.total_amount for b in all_bills)

    # 🔥 TOTAL REVENUE (paid amount of those bills)
    total_revenue = sum(b.total_paid for b in all_bills)

    # 🔥 PENDING AMOUNT (clean + correct)
    pending_amount = sum(
        b.remaining_amount for b in all_bills
        if b.payment_status != "CANCELLED"
    )

    # 🔥 PENDING BILLS COUNT
    pending_bills = all_bills.filter(
        payment_status__in=["UNPAID", "PARTIAL"]
    ).count()

    # ---------------- PAYMENTS (FOR CHART ONLY) ----------------
    payments = Payment.objects.filter(
        created_at__range=[
            datetime.combine(start_date, time.min),
            datetime.combine(end_date, time.max)
        ],
        is_deleted=False
    )

    # ---------------- CHART ----------------
    chart_data = (
        payments
        .values("created_at__date")
        .annotate(total=Sum("amount"))
        .order_by("created_at__date")
    )

    chart_map = {
        item["created_at__date"]: float(item["total"] or 0)
        for item in chart_data
    }

    days = []
    sales = []

    current = start_date
    while current <= end_date:
        days.append(current.strftime("%d %b"))
        sales.append(chart_map.get(current, 0))
        current += timedelta(days=1)

    # ---------------- TOP PRODUCTS ----------------
    top_products = (
        BillItem.objects
        .filter(
            bill__payment_status="PAID",
            bill__created_at__date__range=[start_date, end_date]
        )
        .values("product__name")
        .annotate(total_sold=Sum("quantity"))
        .order_by("-total_sold")[:5]
    )

    # ---------------- PAYMENT METHODS ----------------
    payment_methods = (
        payments
        .values("method")
        .annotate(total=Sum("amount"))
    )

    # ---------------- TOP CUSTOMERS ----------------
    top_customers = (
        payments
        .values("bill__customer_name", "bill__customer__name")
        .annotate(total_spent=Sum("amount"))
        .order_by("-total_spent")[:5]
    )

    # ---------------- FORMAT ----------------
    product_names = [p["product__name"] for p in top_products]
    product_sales = [p["total_sold"] for p in top_products]

    method_labels = [p["method"] for p in payment_methods]
    method_data = [float(p["total"]) for p in payment_methods]

    customer_labels = [
        c["bill__customer_name"] or c["bill__customer__name"] or "Unknown"
        for c in top_customers
    ]
    customer_data = [float(c["total_spent"] or 0) for c in top_customers]

    # ---------------- CONTEXT ----------------
    context = {
        "pending_bills": pending_bills,
        "total_bills": total_bills,
        "paid_bills": paid_bills,
        "cancelled_bills": cancelled_bills,

        # 🔥 FIXED VALUES
        "total_sales": total_sales,
        "total_revenue": total_revenue,
        "pending_amount": pending_amount,

        "days": days,
        "sales": sales,

        "product_names": product_names,
        "product_sales": product_sales,

        "method_labels": method_labels,
        "method_data": method_data,

        "customer_labels": customer_labels,
        "customer_data": customer_data,

        "start_date": start_date,
        "end_date": end_date,
    }

    return render(request, "reports/reports_dashboard.html", context)
# ===================== CSV EXPORT =====================

def export_report_csv(request):

    today = now().date()

    range_filter = request.GET.get("range")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    # ---------------- DATE FILTER ----------------
    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        except:
            return HttpResponse("Invalid date")

    elif range_filter == "today":
        start_date = today
        end_date = today

    elif range_filter == "week":
        start_date = today - timedelta(days=6)
        end_date = today

    elif range_filter == "month":
        start_date = today.replace(day=1)
        end_date = today

    else:
        start_date = today - timedelta(days=6)
        end_date = today

    # ---------------- DATA ----------------
    bills = Bill.objects.filter(
        created_at__date__range=[start_date, end_date],
        payment_status="PAID"
    ).prefetch_related("payments", "customer")

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="report.csv"'

    writer = csv.writer(response)

    # HEADER
    writer.writerow(["BrainyBeam Sales Report"])
    writer.writerow([f"Date Range: {start_date} to {end_date}"])
    writer.writerow([f"Generated On: {today}"])
    writer.writerow([])

    writer.writerow([
        "Bill ID",
        "Invoice No",
        "Customer",
        "Date",
        "Amount",
        "Status"
    ])

    total = 0
    total_bills = 0

    for bill in bills:
        customer_name = bill.customer_name or (bill.customer.name if bill.customer else "")

        bill_total = sum(p.amount for p in bill.payments.all() if not p.is_deleted)

        total += bill_total
        total_bills += 1

        writer.writerow([
            bill.id,
            bill.invoice_number,
            customer_name,
            bill.created_at.strftime("%Y-%m-%d"),
            bill_total,
            bill.payment_status
        ])

    writer.writerow([])
    writer.writerow(["SUMMARY"])
    writer.writerow(["Total Bills", total_bills])
    writer.writerow(["Total Revenue", total])

    return response


# ===================== PDF EXPORT =====================

def export_report_pdf(request):

    today = now().date()

    range_filter = request.GET.get("range")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    # ---------------- DATE FILTER ----------------
    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        except:
            return HttpResponse("Invalid date")

    elif range_filter == "today":
        start_date = today
        end_date = today

    elif range_filter == "week":
        start_date = today - timedelta(days=6)
        end_date = today

    elif range_filter == "month":
        start_date = today.replace(day=1)
        end_date = today

    else:
        start_date = today - timedelta(days=6)
        end_date = today

    # ---------------- DATA ----------------
    bills = Bill.objects.filter(
        created_at__date__range=[start_date, end_date],
        payment_status="PAID"
    ).prefetch_related("payments", "customer")

    total = 0
    total_bills = 0

    for bill in bills:
        bill_total = sum(p.amount for p in bill.payments.all() if not p.is_deleted)
        total += bill_total
        total_bills += 1

    template = get_template("reports/report_pdf.html")

    html = template.render({
        "bills": bills,
        "total": total,
        "total_bills": total_bills,
        "start_date": start_date,
        "end_date": end_date,
        "generated_on": today,
    })

    response = HttpResponse(content_type="application/pdf")
    response['Content-Disposition'] = 'attachment; filename="report.pdf"'

    pisa.CreatePDF(html, dest=response)

    return response


