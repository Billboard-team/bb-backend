from django.urls import path
from . import views
from . import auth_views

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
    path("me/", auth_views.me_view),
    path("me/update/", auth_views.update_profile_view),
    path("auth0-logs/", auth_views.auth0_log_webhook),
    path("me/delete/", auth_views.delete_account_view),

    # Comment endpoints
    path("bills/<int:bill_id>/comments/", views.get_bill_comments, name="get_bill_comments"),
    path("bills/<int:bill_id>/comments/add/", views.add_bill_comment, name="add_bill_comment"),
    path("bills/<int:bill_id>/comments/<int:comment_id>/", views.manage_comment, name="manage_comment"),
    path("bills/<int:bill_id>/comments/<int:comment_id>/like/", views.like_comment, name="like_comment"),
    path("bills/<int:bill_id>/comments/<int:comment_id>/dislike/", views.dislike_comment, name="dislike_comment"),
]


