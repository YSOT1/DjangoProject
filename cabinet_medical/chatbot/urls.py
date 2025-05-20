from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_interface, name='chat_interface'),
    path('process_message/', views.process_message, name='process_message'),
    path('chat_history/', views.get_chat_history, name='get_chat_history'),
] 