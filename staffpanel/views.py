from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.core.paginator import Paginator
from django.template.loader import get_template, render_to_string
from django.urls import reverse
from django.utils.timezone import now
from django.db.models import F, Q, Case, When, IntegerField, Value
from django.db.models.functions import Coalesce, Lower
from xhtml2pdf import pisa
import os
import json
from datetime import timedelta
from django.contrib.messages import get_messages
from billing.models import Bill, BillItem
from customers.models import Customer
from products.models import Product
from .forms import InvoiceForm
from products.forms import ProductForm
from customers.forms import CustomerForm
from account.utils import role_required


# ---------------- DASHBOARD ----------------

@role_required(["ADMIN", "STAFF"])
def dashboard(request):

    total_bills = Bill.objects.count()
    paid_bills = Bill.objects.filter(payment_status="PAID").count()
    unpaid_bills = Bill.objects.filter(payment_status="UNPAID").count()
    total_customers = Customer.objects.count()
    total_products = Product.objects.count()

    today = now().date()

    # ✅ COUNT (for dashboard card)
    today_bills = Bill.objects.filter(created_at__date=today).count()

    # ---------------- SALES CHART ----------------
    last_7_days = []
    sales_data = []

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)

        day_bills = Bill.objects.filter(
            created_at__date=day,
            payment_status="PAID"
        )

        # ✅ FIXED (removed ())
        total = sum(float(b.total_amount) for b in day_bills)

        last_7_days.append(day.strftime("%a"))
        sales_data.append(total)

    # ---------------- TODAY SALES ----------------
    today_paid_bills = Bill.objects.filter(
        created_at__date=today,
        payment_status="PAID"
    )

    # ✅ FIXED
    today_sales = sum(bill.total_amount for bill in today_paid_bills)

    # ---------------- TOTAL REVENUE ----------------
    all_paid_bills = Bill.objects.filter(payment_status="PAID")

    # ✅ FIXED
    total_revenue = sum(bill.total_amount for bill in all_paid_bills)

    total_orders = all_paid_bills.count()

    # ---------------- OTHER DATA ----------------
    recent_bills = Bill.objects.order_by("-created_at")[:5]

    low_stock_count = Product.objects.filter(
        stock_quantity__lte=F("low_stock_threshold")
    ).count()
    
    # ---------------- PENDING AMOUNT  ----------------
    pending_amount = sum(
        bill.remaining_amount
        for bill in Bill.objects.all()
        if bill.remaining_amount > 0 and bill.payment_status != "CANCELLED"
    )

    # Pending Bills Count
    pending_bills_count = Bill.objects.filter(
        payment_status__in=["UNPAID", "PARTIAL"]
    ).count()
    # ---------------- CONTEXT ----------------
    context = {
        "total_customers": total_customers,
        "total_bills": total_bills,
        "paid_bills": paid_bills,
        "unpaid_bills": unpaid_bills,
        "today_sales": today_sales,
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "recent_bills": recent_bills,
        "low_stock_count": low_stock_count,
        "total_products": total_products,
        "context_days": json.dumps(last_7_days),
        "context_sales": json.dumps(sales_data),
        "today_bills": today_bills,
        "pending_amount": pending_amount,
        "pending_bills_count": pending_bills_count,
    }

    return render(request, "staffpanel/dashboard.html", context)

@role_required(["ADMIN", "STAFF", "CASHIER"])
def create_bill(request):

    if request.method == "POST":
        form = InvoiceForm(request.POST)

        if form.is_valid():

            invoice = form.save(commit=False)

            # ✅ DATE
            custom_date = form.cleaned_data.get("created_at")
            invoice.created_at = custom_date if custom_date else now()

            # ✅ DATA
            customer = form.cleaned_data.get("customer")
            name = form.cleaned_data.get("customer_name")
            phone = form.cleaned_data.get("customer_phone")

            save_customer = request.POST.get("save_customer")
            customer_type = request.POST.get("customer_type")

            # ================= EXISTING CUSTOMER =================
            if customer_type == "existing":

                if not customer:
                    messages.error(request, "Please select a customer", extra_tags="create_bill")
                    
                    return render(request, "staffpanel/create_bill.html", {"form": form})

                invoice.customer = customer
                invoice.customer_name = None
                invoice.customer_phone = None

            # ================= WALK-IN CUSTOMER =================
            else:

                if not name:
                    messages.error(request, "Customer name required", extra_tags="create_bill")
                    return render(request, "staffpanel/create_bill.html", {"form": form})

                invoice.customer = None
                invoice.customer_name = name or "Walk-in Customer"
                invoice.customer_phone = phone

                # ✅ SAVE CUSTOMER OPTION
                if save_customer:

                    existing_customer = Customer.objects.filter(phone=phone).first()

                    if existing_customer:
                        messages.warning(request, "Customer with this phone already exists", extra_tags="create_bill")

                        return render(request, "staffpanel/create_bill.html", {"form": form})

                    email = request.POST.get("customer_email")
                    address = request.POST.get("customer_address")

                    new_customer = Customer.objects.create(
                        name=name or "Walk-in Customer",
                        phone=phone,
                        email=email,
                        address=address
                    )

                    invoice.customer = new_customer
                    invoice.customer_name = None
                    invoice.customer_phone = None

            # ================= SAVE BILL =================
            invoice.save()

            return redirect("pos:add_items", bill_id=invoice.id)

    else:
       
        form = InvoiceForm()

    return render(request, "staffpanel/create_bill.html", {"form": form})


@role_required(["ADMIN", "STAFF", "CASHIER"])
def bill_list(request):

    status = request.GET.get("status")
    query = request.GET.get("q", "").strip().lower()
    sort = request.GET.get("sort")

    # ---------------- BASE QUERY ----------------
    bills = Bill.objects.all().prefetch_related("payments")

    # ---------------- SEARCH ----------------
    if query:
        bills = bills.annotate(
            display_name=Lower(Coalesce("customer_name", "customer__name"))
        ).filter(
            Q(display_name__icontains=query) |
            Q(invoice_number__icontains=query)
        ).annotate(
            priority=Case(
                When(display_name__startswith=query, then=Value(0)),
                When(display_name__icontains=query, then=Value(1)),
                default=Value(2),
                output_field=IntegerField()
            )
        )

    # ---------------- FILTER ----------------
    if status in ["PAID", "UNPAID", "CANCELLED", "DRAFT", "PARTIAL"]:
        bills = bills.filter(payment_status=status)

    # ---------------- SORTING ----------------
    if query:
        # 🔥 Search priority + sorting (DB level, NO Python sorted)
        if sort == "oldest":
            bills = bills.order_by("priority", "display_name", "created_at")
        elif sort == "date":
            bills = bills.order_by("priority", "display_name", "-created_at")
        else:
            bills = bills.order_by("priority", "display_name", "-id")
    else:
        # Normal sorting
        if sort == "oldest":
            bills = bills.order_by("created_at")
        elif sort == "date":
            bills = bills.order_by("-created_at")
        else:
            bills = bills.order_by("-id")

    # ---------------- PAGINATION ----------------
    paginator = Paginator(bills, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "selected_status": status,
        "search_query": query,
        "selected_sort": sort,
    }

    # ---------------- AJAX ----------------
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string(
            "staffpanel/partials/bill_table_body.html",
            {"page_obj": page_obj, "selected_status": status},
            request=request
        )
        return JsonResponse({"html": html})

    return render(request, "staffpanel/bill_list.html", context)

# ---------------- TOGGLE PAID / UNPAID ----------------
@role_required(["ADMIN", "STAFF", "CASHIER"])
def toggle_bill_status(request, pk):

    bill = get_object_or_404(Bill, pk=pk)

    # Draft → Unpaid
    if bill.payment_status == "DRAFT":
        bill.payment_status = "UNPAID"

    # Unpaid → Paid
    elif bill.payment_status == "UNPAID":
        bill.payment_status = "PAID"

    # Paid → Unpaid (optional)
    elif bill.payment_status == "PAID":
        bill.payment_status = "UNPAID"

    bill.save()

    return redirect("staffpanel:bill_list")



# ---------------- CANCEL BILL ----------------
@role_required(["ADMIN", "STAFF", "CASHIER"])
def cancel_bill(request, pk):
    bill = get_object_or_404(Bill, pk=pk)

    page = request.GET.get("page", 1)

    if request.method == "POST":

        if bill.payment_status != "CANCELLED":

            # 🔄 restore stock
            for item in bill.items.all():
                product = item.product
                product.stock_quantity += item.quantity
                product.save()

            # ✅ cancel
            bill.payment_status = "CANCELLED"

            # ✅ remove QR
            if bill.qr_code:
                bill.qr_code.delete(save=False)
                bill.qr_code = None

            bill.save()

            messages.success(request, "Bill cancelled successfully!")


        url = reverse("staffpanel:bill_list")
        return redirect(f"{url}?page={page}")

    return redirect(f"/staffpanel/bills/?page={page}")


# ---------------- INVOICE PDF ----------------
@role_required(["ADMIN", "STAFF", "CASHIER"])
def invoice_pdf(request, invoice_number):

    bill = get_object_or_404(Bill, invoice_number=invoice_number)

    items = bill.items.all()

    qr_path = None

    if bill.qr_code:
        qr_path = os.path.join(settings.MEDIA_ROOT, bill.qr_code.name)

    template = get_template("staffpanel/invoice_pdf.html")

    html = template.render({
        "bill": bill,
        "items": items,
        "qr_path": qr_path
    })

    response = HttpResponse(content_type="application/pdf")

    response["Content-Disposition"] = f'attachment; filename="invoice_{bill.invoice_number}.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse("Error generating PDF")

    return response




@role_required(["ADMIN", "STAFF", "CASHIER"])
def delete_bill(request, pk):

    bill = get_object_or_404(Bill, pk=pk)

    if bill.payment_status == "DRAFT":
        bill.delete()

    return redirect("staffpanel:bill_list")


@login_required
def bill_search_suggestions(request):
    query = request.GET.get("q", "").strip().lower()

    results = []

    if query:
        bills = Bill.objects.annotate(
            name=Lower(Coalesce("customer_name", "customer__name"))
        ).filter(name__icontains=query)[:5]

        for b in bills:
            display_name = b.customer_name or (b.customer.name if b.customer else "")
            results.append({
                "id": b.id,
                "name": display_name,
                "invoice": b.invoice_number
            })

    return JsonResponse({"results": results})

from django.http import JsonResponse
from customers.models import Customer

def customer_search(request):
    query = request.GET.get("q", "")

    customers = Customer.objects.filter(
        name__icontains=query
    ) | Customer.objects.filter(
        phone__icontains=query
    )

    customers = customers[:10]

    results = []
    for c in customers:
        results.append({
            "id": c.id,
            "text": f"{c.name} ({c.phone})" if c.phone else c.name
        })

    return JsonResponse({"results": results})