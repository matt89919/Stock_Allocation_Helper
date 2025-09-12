# portfolio_tracker/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# 建立一個 router 並註冊我們的 viewsets
router = DefaultRouter()
router.register(r'stocks', views.StockViewSet)
router.register(r'options', views.OptionViewSet)
router.register(r'holdings', views.HoldingViewSet)
router.register(r'alerts', views.PriceAlertViewSet)

# API URL 會由 router 自動產生
urlpatterns = [
    path('', include(router.urls)),
]