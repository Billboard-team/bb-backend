from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("bills/trending", views.trending_bills, name="trending_bills"),
    path("bills/recommended", views.recommended_bills, name="recommended_bills"),

]
