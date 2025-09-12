# config/urls.py
from django.contrib import admin
from django.urls import path, include # 確保 include 被匯入

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('portfolio_tracker.urls')),
]