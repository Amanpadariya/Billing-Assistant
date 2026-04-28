from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from staffpanel.views import dashboard
from django.views.generic.base import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(url='/account/login/'), name='home'),
    path('admin/', admin.site.urls),
    path('account/', include('account.urls')),
    path('', dashboard, name='home'),
    path('billing/', include(('billing.urls', 'billing'), namespace='billing')),
    path('staffpanel/', include('staffpanel.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path("customers/", include("customers.urls")),
    path('products/', include('products.urls')),
    path("pos/", include("pos.urls")),
    path("reports/", include("reports.urls")),
    path("payments/", include("payments.urls")),
]

# Serve media files in both dev and production
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)