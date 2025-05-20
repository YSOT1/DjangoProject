from django.urls import path
from . import views

urlpatterns = [
    path('process-payment/<int:invoice_id>/', views.process_payment, name='process_payment'),
    path('financial-dashboard/', views.doctor_financial_dashboard, name='doctor_financial_dashboard'),
    path('earnings-chart-data/', views.get_earnings_chart_data, name='get_earnings_chart_data'),
    path('print-invoice/<int:invoice_id>/', views.print_invoice, name='print_invoice'),
]
