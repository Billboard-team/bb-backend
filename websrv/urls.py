from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("bills/trending", views.trending_bills, name="trending_bills"),
    path("bills/trending/education", views.trending_bills_education, name="trending_bills_education"),
    path("bills/recommended", views.recommended_bills, name="recommended_bills"),

    path("bills/<int:id>", views.single_bill, name="single_bill"),
    path("bills/<int:id>/cosponsors", views.bill_cosponsors, name="bill_cosponsors"),

    path("bills/<int:id>/text", views.get_bill_text_original, name="bill_text_original"),  
    path("bills/<int:id>/text/summarized", views.get_bill_text_summarized, name="bill_text_summarized"),  
    path("bills/<int:id>/text/sources", views.get_bill_text_sources, name="bill_text_sources"),  
]


