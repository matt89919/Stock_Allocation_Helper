# portfolio_tracker/views.py
from rest_framework import viewsets
from .models import Stock, Option, Holding, PriceAlert
from .serializers import (
    StockSerializer, OptionSerializer, HoldingSerializer, PriceAlertSerializer
)

# ModelViewSet 會自動提供 list, create, retrieve, update, delete 功能
class StockViewSet(viewsets.ModelViewSet):
    queryset = Stock.objects.all()
    serializer_class = StockSerializer

class OptionViewSet(viewsets.ModelViewSet):
    queryset = Option.objects.all()
    serializer_class = OptionSerializer

class HoldingViewSet(viewsets.ModelViewSet):
    queryset = Holding.objects.all()
    serializer_class = HoldingSerializer

class PriceAlertViewSet(viewsets.ModelViewSet):
    queryset = PriceAlert.objects.all()
    serializer_class = PriceAlertSerializer