from django.urls import path
from django.contrib.auth.views import LoginView
from .views import custom_logout
from . import views
from .views import redirect_after_login

app_name = "account"

urlpatterns = [
    path('login/', LoginView.as_view(
        template_name='registration/login.html'
    ), name='login'),
    path('logout/', custom_logout, name='logout'),
    path('manage-users/', views.manage_users, name='manage_users'),
    path('add-user/', views.add_user, name='add_user'),
    path('edit-user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('redirect/', views.redirect_after_login, name='redirect_after_login'),
]