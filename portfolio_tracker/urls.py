from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our new viewsets
router = DefaultRouter()
router.register(r'stocks', views.StockViewSet)
router.register(r'options', views.OptionViewSet)
router.register(r'holdings', views.HoldingViewSet)
router.register(r'portfolio-history', views.PortfolioHistoryViewSet, basename='portfolio-history')

# --- NEW ENDPOINTS REGISTERED HERE ---
router.register(r'deposits', views.DepositViewSet, basename='deposit')
router.register(r'transactions', views.TransactionViewSet, basename='transaction')

urlpatterns = [
    # The router now automatically handles all URL patterns for the ViewSets
    path('', include(router.urls)),
    
    # Add the new path for the summary data view
    path('portfolio-summary/', views.portfolio_summary_view, name='portfolio-summary'),
]

