from django.urls import path
from .views import FinancialDataExtractionView

urlpatterns = [
    path('extract/', FinancialDataExtractionView.as_view(), name='financial-data-extract'),
]