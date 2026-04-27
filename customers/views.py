from django.shortcuts import render, redirect, get_object_or_404

from account.utils import role_required
from .models import Customer
from billing.models import Bill
from django.contrib.auth.decorators import login_required
from .forms import CustomerForm
from django.contrib import messages


@role_required(["ADMIN", "STAFF", "CASHIER"])
def customer_list(request):
    customers = Customer.objects.order_by("-created_at")
    return render(request, "customers/customer_list.html", {"customers": customers})


@role_required(["ADMIN", "STAFF", "CASHIER"])
def add_customer(request):
    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Customer added successfully.")
            return redirect("customers:customer_list")
    else:
        form = CustomerForm()

    return render(request, "customers/customer_form.html", {"form": form})


@role_required(["ADMIN", "STAFF", "CASHIER"])
def edit_customer(request, pk):
    customer = get_object_or_404(Customer, pk=pk)

    if request.method == "POST":
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, "Customer updated.")
            return redirect("customers:customer_list")
    else:
        form = CustomerForm(instance=customer)

    return render(request, "customers/customer_form.html", {"form": form})


@role_required(["ADMIN", "STAFF", "CASHIER"])
def delete_customer(request, pk):
    customer = get_object_or_404(Customer, pk=pk)

    if customer.is_walkin:
        messages.error(request, "Walk-in customer cannot be deleted.")
        return redirect("customers:customer_list")

    customer.delete()
    messages.success(request, "Customer deleted successfully.")
    return redirect("customers:customer_list")


@role_required(["ADMIN", "STAFF", "CASHIER"])
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    bills = Bill.objects.filter(customer=customer)

    context = {
        "customer": customer,
        "bills": bills,
        "total_bills": bills.count(),
        "total_paid": bills.filter(payment_status="PAID").count(),
        "total_unpaid": bills.filter(payment_status="UNPAID").count(),
        "total_amount": sum(b.total_amount for b in bills),
    }

    return render(request, "customers/customer_detail.html", context)
