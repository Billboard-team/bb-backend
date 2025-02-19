from django.urls import path
from . import views

urlpatterns = [
    path("home", views.index, name="index"),
    path("home/trending_bills", views.trending_bills, name="trending_bills"),
    path("home/recommended_bills", views.recommended_bills, name="recommended_bills"),

]
