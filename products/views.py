from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from account.utils import role_required
from .models import Product
from .forms import ProductForm


@role_required(["ADMIN", "STAFF"])
def product_list(request):
    products = Product.objects.order_by("-id")
    return render(request, "products/product_list.html", {"products": products})


@role_required(["ADMIN", "STAFF"])
def add_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Product added.")
            return redirect("products:product_list")
    else:
        form = ProductForm()

    return render(request, "products/product_form.html", {"form": form})


@role_required(["ADMIN", "STAFF"])
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated.")
            return redirect("products:product_list")
    else:
        form = ProductForm(instance=product)

    return render(request, "products/product_form.html", {"form": form})


@role_required(["ADMIN", "STAFF"])
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    messages.success(request, "Product deleted.")
    return redirect("products:product_list")