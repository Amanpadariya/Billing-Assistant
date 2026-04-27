from django.urls import path
from . import views   # ✅ FIXED

app_name = "pos"

urlpatterns = [
    path("", views.pos_page, name="pos_page"),
    path("add/<uuid:bill_id>/", views.add_items, name="add_items"),
    path("quick/<uuid:bill_id>/<int:product_id>/", views.quick_add_product),
    path("delete/<int:item_id>/", views.delete_item),
    path("update/<int:item_id>/", views.update_item),
]