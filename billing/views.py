from django.shortcuts import render, redirect, get_object_or_404
from .models import Bill
from customers.models import Customer




# ---------------- PUBLIC: INVOICE DETAIL ----------------
# No @login_required — customers access this via QR code scan
def invoice_detail(request, invoice_number):

    bill = get_object_or_404(Bill, invoice_number=invoice_number)

    # Convert draft → unpaid on first view
    if bill.payment_status == "DRAFT":
        bill.payment_status = "UNPAID"
        bill.save(update_fields=["payment_status"])

    # Only regenerate QR if it's missing (avoids duplicate files)
    if not bill.qr_code and bill.remaining_amount > 0:
        bill.generate_qr()
        bill.save(update_fields=["qr_code"])

    items = bill.items.all()

    return render(request, "billing/invoice_detail.html", {
        "bill": bill,
        "items": items,
    })


# ---------------- PUBLIC: CUSTOMER BILL HISTORY ----------------

def customer_history(request, phone):
    customer = get_object_or_404(Customer, phone=phone)
    bills = Bill.objects.filter(customer=customer)

    return render(request, "billing/customer_history.html", {
        "customer": customer,
        "bills": bills
    })
