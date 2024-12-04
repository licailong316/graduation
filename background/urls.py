from django.urls import path
from background import views

urlpatterns = [
    path('', views.index)
]