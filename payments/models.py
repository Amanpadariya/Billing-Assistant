from django.db import models
from billing.models import Bill


class Payment(models.Model):

    METHOD_CHOICES = [
        ('CASH', 'Cash'),
        ('UPI', 'UPI'),
        ('CARD', 'Card'),
    ]

    bill = models.ForeignKey(
        Bill,
        on_delete=models.CASCADE,
        related_name='payments'
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    method = models.CharField(
        max_length=10,
        choices=METHOD_CHOICES
    )

    created_at = models.DateTimeField(auto_now_add=True)

    is_deleted = models.BooleanField(default=False)

    # ✅ AUTO UPDATE BILL STATUS AFTER PAYMENT
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Update bill payment status
        self.bill.update_payment_status()
        self.bill.save(update_fields=["payment_status"])

    def __str__(self):
        return f"Payment {self.amount} for Bill {self.bill.id}"