from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import auth_views
from .comment_views import CommentViewSet

router = DefaultRouter()
router.register(r'comments', CommentViewSet, basename='comment')

urlpatterns = [
    path("", views.index, name="index"),

    path("bills/trending", views.trending_bills, name="trending_bills"),
    path("bills/recommended", views.recommended_bills, name="recommended_bills"),

    path("members/<str:bioguide_id>", views.get_member_data, name="member_detailed_view"),  
    path("congress/<str:congress>", views.congress_members, name="congress_members"),

    path("bills/<int:id>", views.get_bill_detailed, name="bill_detailed_view"),  

    path("bills/<int:id>/text", views.get_bill_text_original, name="bill_text_original"),  
    path("bills/<int:id>/text/summarized", views.get_bill_text_summarized, name="bill_text_summarized"),  
    path("bills/<int:id>/text/sources", views.get_bill_text_sources, name="bill_text_sources"),  

    path("me/", auth_views.me_view),
    path("me/update/", auth_views.update_profile_view),
    path("auth0-logs/", auth_views.auth0_log_webhook),
    path("me/delete/", auth_views.delete_account_view),
    path('me/activity-stats/', views.get_user_activity_stats, name='get_user_activity_stats'),

    path('bills/<int:id>/view/', views.record_bill_view, name='record_bill_view'),
    path('bills/view-history/', views.get_bill_view_history, name='get_bill_view_history'),

    path('bills/<int:id>/check-liked/', views.check_if_liked_bill, name='check_liked'),
    path('bills/<int:id>/like-bill/', views.like_bill, name='like_bill'),
    path('bills/<int:id>/unlike-bill/', views.unlike_bill, name='unlike_bill'),

    # Include DRF router URLs (includes all comment endpoints)
    path('', include(router.urls)),
]
