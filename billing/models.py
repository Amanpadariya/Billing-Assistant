from django.db import models, transaction, IntegrityError
import uuid
import qrcode
from io import BytesIO
from decimal import Decimal
from django.conf import settings
from django.core.files import File
from django.db.models import F, Sum
from django.utils.timezone import now
from datetime import datetime




class Bill(models.Model):

    # ✅ Keep UUID as primary key (safe + internal)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # ✅ Professional invoice number (user-friendly)
    invoice_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    # ---------------- CUSTOMER ----------------
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    customer_name = models.CharField(max_length=100, blank=True, null=True)
    customer_phone = models.CharField(max_length=20, blank=True, null=True)

    created_at = models.DateTimeField(default=now)

    # ---------------- PAYMENT STATUS ----------------
    PAYMENT_CHOICES = [
        ("DRAFT", "Draft"),
        ("UNPAID", "Unpaid"),
        ("PARTIAL", "Partial"),
        ("PAID", "Paid"),
        ("CANCELLED", "Cancelled"),
    ]

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_CHOICES,
        default="DRAFT"
    )

    qr_code = models.ImageField(upload_to="qr_codes/", blank=True, null=True)

    # ---------------- BILL TOTAL ----------------
    @property
    def total_amount(self):
        return self.items.aggregate(
            total=Sum(F('quantity') * F('product__price'))
        )['total'] or Decimal("0.00")

    # ---------------- CUSTOMER DISPLAY ----------------
    def display_customer(self):
        if self.customer_name:
            return self.customer_name
        if self.customer:
            return self.customer.name
        return "Walk-in Customer"

    # ---------------- PAYMENT LOGIC ----------------
    @property
    def total_paid(self):
        return self.payments.filter(is_deleted=False).aggregate(
            total=Sum('amount')
        )['total'] or Decimal("0.00")

    @property
    def remaining_amount(self):
        return self.total_amount - self.total_paid

    def update_payment_status(self):

        if self.payment_status == "CANCELLED":
            return

        paid = self.total_paid
        total = self.total_amount

        if paid == 0:
            self.payment_status = "UNPAID"
        elif paid < total:
            self.payment_status = "PARTIAL"
        else:
            self.payment_status = "PAID"

   # ---------------- QR GENERATION ----------------
def generate_qr(self):
    remaining = self.remaining_amount

    if remaining <= 0:
        # Bill is fully paid — delete QR and clear field
        if self.qr_code:
            try:
                self.qr_code.delete(save=False)
            except Exception:
                pass
            self.qr_code = None
        return

    upi_id = getattr(settings, "UPI_ID", "yourname@upi")
    name = getattr(settings, "STORE_NAME", "My Store")

    upi_link = (
        f"upi://pay?pa={upi_id}&pn={name}"
        f"&am={remaining}&tn=Invoice-{self.invoice_number}"
    )

    qr = qrcode.make(upi_link)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")

    # Fixed filename — no random suffix = no duplicates
    file_name = f"qr_{self.invoice_number}.png"

    # Delete old file before saving new one
    if self.qr_code:
        try:
            self.qr_code.delete(save=False)
        except Exception:
            pass

    self.qr_code.save(file_name, File(buffer), save=False)

    # ---------------- SAVE OVERRIDE ----------------
    def save(self, *args, **kwargs):

        # If called with update_fields, skip invoice/status/qr logic — just persist
        if kwargs.get("update_fields"):
            super().save(*args, **kwargs)
            return

        if not self.invoice_number:
            year = datetime.now().year

            for attempt in range(10):  # retry protection
                try:
                    with transaction.atomic():

                        last_bill = Bill.objects.select_for_update().filter(
                            invoice_number__startswith=f"INV-{year}"
                        ).order_by('-created_at').first()

                        last_number = 0
                        if last_bill and last_bill.invoice_number:
                            try:
                                last_part = last_bill.invoice_number.split('-')[-1]
                                last_number = int(last_part)
                            except ValueError:
                                last_number = 0

                        new_number = last_number + 1
                        self.invoice_number = f"INV-{year}-{new_number:03d}"

                        # Compute status + QR before the single DB write
                        self.update_payment_status()
                        self.generate_qr()
                        super().save(*args, **kwargs)
                        return

                except IntegrityError:
                    if attempt == 9:
                        # FINAL FALLBACK (guaranteed unique)
                        unique_part = str(uuid.uuid4())[:6]
                        self.invoice_number = f"INV-{year}-{unique_part}"
                        self.update_payment_status()
                        self.generate_qr()
                        super().save(*args, **kwargs)
                        return
                    continue
        else:
            self.update_payment_status()
            self.generate_qr()
            super().save(*args, **kwargs)

    def __str__(self):
        return f"Invoice {self.invoice_number}"
    
# ---------------- BILL ITEM ----------------
class BillItem(models.Model):
    bill = models.ForeignKey(
        Bill,
        related_name="items",
        on_delete=models.CASCADE
    )

    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def total_price(self):
        return self.product.price * self.quantity