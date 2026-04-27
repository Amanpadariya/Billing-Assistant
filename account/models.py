from django.contrib.auth.models import AbstractUser
from django.db import models
class User(AbstractUser):

    ROLE_CHOICES = (
        ("ADMIN", "Admin"),
        ("STAFF", "Staff"),
        ("CASHIER", "Cashier"),  
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="STAFF")

    def is_admin(self):
        return self.role == "ADMIN"

    def is_staff_user(self):
        return self.role == "STAFF"

    def is_cashier(self):
        return self.role == "CASHIER"