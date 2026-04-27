from decimal import Decimal
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages

from billing.models import Bill
from .models import Payment


# ---------------- ADD PAYMENT ----------------
def add_payment(request, bill_id):

    bill = get_object_or_404(Bill, id=bill_id)

    if request.method == "POST":

        # 🔁 detect redirect target
        next_url = request.POST.get("next")
        page = request.POST.get("page", 1)

        # ❌ BLOCK CANCELLED BILL
        if bill.payment_status == "CANCELLED":
            messages.error(request, "Cannot add payment to a cancelled bill.")
            return redirect(next_url or f"/staffpanel/bills/?page={page}#bill{bill.id}")

        try:
            amount = Decimal(request.POST.get("amount"))
        except:
            messages.error(request, "Invalid amount.")
            return redirect(next_url or f"/staffpanel/bills/?page={page}#bill{bill.id}")

        method = request.POST.get("method")

        total_paid = bill.total_paid
        total_amount = bill.total_amount

        # ❌ FULLY PAID BLOCK
        if total_paid >= total_amount:
            messages.warning(request, "This bill is already fully paid.")
            return redirect(next_url or f"/staffpanel/bills/?page={page}#bill{bill.id}")

        # ❌ OVERPAY BLOCK
        if total_paid + amount > total_amount:
            remaining = total_amount - total_paid
            messages.error(
                request,
                f"Only ₹{remaining} remaining. Cannot exceed total."
            )
            return redirect(next_url or f"/staffpanel/bills/?page={page}#bill{bill.id}")

        # ✅ CREATE PAYMENT
        Payment.objects.create(
            bill=bill,
            amount=amount,
            method=method
        )

        # ✅ JUST SAVE BILL → triggers:
        # update_payment_status + generate_qr automatically
        bill.save()

        messages.success(request, "Payment added successfully!")

        return redirect(next_url or f"/staffpanel/bills/?page={page}#bill{bill.id}")


# ---------------- PAYMENT LIST ----------------
def bill_payments(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id)

    payments = bill.payments.filter(is_deleted=False).order_by("-created_at")
    page = request.GET.get("page", 1)

    return render(request, "payments/bill_payments.html", {
        "bill": bill,
        "payments": payments
    })


# ---------------- DELETE PAYMENT ----------------
def delete_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    bill = payment.bill

    # ❌ prevent double delete
    if payment.is_deleted:
        messages.warning(request, "Payment already removed.")
        return redirect("payments:bill_payments", bill_id=bill.id)

    # ✅ soft delete
    payment.is_deleted = True
    payment.save()

    # ✅ recalc using properties (not method calls)
    bill.update_payment_status()
    bill.generate_qr()
    bill.save(update_fields=["payment_status", "qr_code"])

    messages.success(request, "Payment removed successfully!")

    return redirect("payments:bill_payments", bill_id=bill.id)
