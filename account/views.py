from django.shortcuts import render,redirect
from django.contrib.auth import logout
from account.utils import role_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.shortcuts import redirect


@role_required(["ADMIN", "STAFF", "CASHIER"])
def staff_dashboard(request):
    return render(request, "account/dashboard.html")


def custom_logout(request):
    logout(request)
    return redirect('account:login')


User = get_user_model()

@role_required(["ADMIN"])
def manage_users(request):
    users = User.objects.all().order_by("-date_joined")
    return render(request, "account/manage_users.html", {"users": users})



@role_required(["ADMIN"])
def add_user(request):

    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        role = request.POST.get("role")

        if not username or not password:
            messages.error(request, "Username and password required")
            return redirect("account:add_user")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect("account:add_user")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=role
        )

        messages.success(request, "User created successfully")
        return redirect("account:manage_users")

    return render(request, "account/add_user.html")

@role_required(["ADMIN"])
def edit_user(request, user_id):
    user = User.objects.get(id=user_id)

    if request.method == "POST":
        role = request.POST.get("role")

        user.role = role
        user.save()

        messages.success(request, "User updated successfully")
        return redirect("account:manage_users")

    return render(request, "account/edit_user.html", {"user": user})

@role_required(["ADMIN"])
def delete_user(request, user_id):
    user = User.objects.get(id=user_id)

    if user.is_superuser:
        return redirect("account:manage_users")

    user.delete()
    messages.success(request, "User deleted successfully")

    return redirect("account:manage_users")


def redirect_after_login(request):
    user = request.user

    if user.role == "CASHIER":
        return redirect("pos:pos_page")

    return redirect("staffpanel:dashboard")