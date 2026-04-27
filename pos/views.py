from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from billing.models import Bill, BillItem
from products.models import Product
from django.contrib import messages
import json
from account.utils import role_required

@role_required(["ADMIN", "STAFF", "CASHIER"])
def add_items(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id)
    products = Product.objects.filter(is_active=True)

    # ✅ GET PAGE + STATUS
    page = request.GET.get("page", 1)
    status = request.GET.get("status", "")

    # ❌ BLOCK EDIT
    if bill.payment_status in ["PAID", "CANCELLED"]:
        messages.error(request, "This bill cannot be edited.")
        return redirect(f"/staffpanel/bills/?page={page}&status={status}")

    items = bill.items.all()
    # ✅ Update bill after items change
    bill.update_payment_status()
    bill.generate_qr()
    bill.save(update_fields=["payment_status", "qr_code"])

    return render(request, "pos/add_items.html", {
        "bill": bill,
        "items": items,
        "products": products,
        "page": page,        # ✅ PASS TO TEMPLATE
        "status": status,    # ✅ PASS TO TEMPLATE
    })

@role_required(["ADMIN", "STAFF", "CASHIER"])
def quick_add_product(request, bill_id, product_id):
    bill = get_object_or_404(Bill, id=bill_id)
    product = get_object_or_404(Product, id=product_id)

    if product.stock_quantity <= 0:
        return JsonResponse({"error": "Out of stock"})

    item, created = BillItem.objects.get_or_create(
        bill=bill,
        product=product,
        defaults={"quantity": 1}
    )

    if not created:
        item.quantity += 1
        item.save()

    product.stock_quantity -= 1
    product.save()

    # ✅ IMPORTANT RESPONSE
    return JsonResponse({
        "item_id": item.id,
        "product_name": product.name,
        "quantity": item.quantity,
        "item_total": item.total_price
    })

@role_required(["ADMIN", "STAFF", "CASHIER"])
def delete_item(request, item_id):
    item = get_object_or_404(BillItem, id=item_id)

    product = item.product
    product.stock_quantity += item.quantity
    product.save()

    item.delete()

    return JsonResponse({"success": True})


@role_required(["ADMIN", "STAFF", "CASHIER"])
def update_item(request, item_id):
    item = get_object_or_404(BillItem, id=item_id)
    data = json.loads(request.body)

    change = int(data.get("change", 0))
    product = item.product

    if change == 1:
        if product.stock_quantity <= 0:
            return JsonResponse({"error": "No stock"})
        item.quantity += 1
        product.stock_quantity -= 1

    elif change == -1:
        if item.quantity > 1:
            item.quantity -= 1
            product.stock_quantity += 1
        else:
            item.delete()
            product.stock_quantity += 1
            product.save()
            return JsonResponse({"deleted": True})

    item.save()
    product.save()

    return JsonResponse({
    "item_id": item.id,
    "quantity": item.quantity,
    "item_total": item.total_price
})



@role_required(["ADMIN", "STAFF", "CASHIER"])
def pos_page(request):
    return render(request, "pos/pos.html")