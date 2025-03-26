from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import UserProfile
from .serializers import UserProfileSerializer


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    auth0_id = request.user.sub

    try:
        user = UserProfile.objects.get(auth0_id=auth0_id)
    except UserProfile.DoesNotExist:
        # 👇 Automatically create user on first login
        user = UserProfile.objects.create(
            auth0_id=auth0_id,
            name=getattr(request.user, "name", "Anonymous"),
            email=getattr(request.user, "email", ""),
            avatar="",  # You could also try to fetch from request.user.picture if included in JWT
            expertise_tags=[],
        )

    return Response(UserProfileSerializer(user).data)
