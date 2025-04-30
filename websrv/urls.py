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

    path("bills/<int:id>", views.get_bill_detailed, name="bill_detailed_view"),  

    path("bills/<int:id>/text", views.get_bill_text_original, name="bill_text_original"),  
    path("bills/<int:id>/text/summarized", views.get_bill_text_summarized, name="bill_text_summarized"),  
    path("bills/<int:id>/text/sources", views.get_bill_text_sources, name="bill_text_sources"),  

    path("me/", auth_views.me_view),
    path("me/update/", auth_views.update_profile_view),
    path("auth0-logs/", auth_views.auth0_log_webhook),
    path("me/delete/", auth_views.delete_account_view),

    path("users/<str:username>/", auth_views.user_profile_view, name="user-profile"),
    path("users/<str:username>/follow/", auth_views.follow_user),
    path("users/<str:username>/is-following/", auth_views.is_following_user),
    path("me/following/", auth_views.my_following),
    path("me/followers/", auth_views.my_followers),
    path("search-users/", auth_views.search_users),

    path("notifications/", auth_views.get_notifications, name="get-notifications"),
    path("notifications/<int:notification_id>/read/", auth_views.mark_notification_read, name="mark-notification-read"),



    # Include DRF router URLs (includes all comment endpoints)
    path('', include(router.urls)),
]
