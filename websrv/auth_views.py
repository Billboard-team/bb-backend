from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import UserProfile
from .serializers import UserProfileSerializer
from django.http import HttpResponse
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
import json

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    user = request.user  # 

    auth0_id = user.sub
    profile, created = UserProfile.objects.get_or_create(
        auth0_id=auth0_id,
        defaults={
            "name": user.name or "",
            "email": user.email or "",
            "avatar": "",
            "expertise_tags": [],
        },
    )
    serializer = UserProfileSerializer(profile)
    return Response(serializer.data)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_profile_view(request):
    auth0_id = request.user.sub
    user = UserProfile.objects.get(auth0_id=auth0_id)

    name = request.data.get("name", "").strip()
    if not name:
        return Response({"error": "Name is required."}, status=400)

    user.name = name
    user.save()
    return Response(UserProfileSerializer(user).data)

@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def auth0_log_webhook(request):
    try:
        # Parse NDJSON (new line-delimited JSON logs)
        raw_body = request.body.decode("utf-8").strip()
        logs = [json.loads(line) for line in raw_body.splitlines()]

        deleted_count = 0
        for log in logs:
            if log.get("type") == "sdu":  # "sdu" = successful deletion
                auth0_id = log.get("user_id")
                print(f"💀 Deletion log received for Auth0 user: {auth0_id}")
                deleted, _ = UserProfile.objects.filter(auth0_id=auth0_id).delete()
                deleted_count += deleted

        return JsonResponse(
            {"status": "ok", "deleted_users": deleted_count},
            status=200,
        )

    except Exception as e:
        return JsonResponse(
            {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
        )
@api_view(["GET"])
@permission_classes([AllowAny])
def list_expertise_tags(request):
    # Hardcode a list of available tags
    tags = ["AI", "Backend", "Finance", "Security", "Healthcare", "Environment"]
    return Response(tags)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_expertise_tags(request):
    from .models import UserProfile

    auth0_id = request.user.sub
    profile = UserProfile.objects.get(auth0_id=auth0_id)

    tags = request.data.get("tags", [])
    if not isinstance(tags, list):
        return Response({"error": "Tags must be a list."}, status=400)

    profile.expertise_tags = tags
    profile.save()
    return Response({"message": "Expertise tags updated."})   

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_profile_view(request):
    auth0_id = request.user.sub
    profile = UserProfile.objects.get(auth0_id=auth0_id)

    new_name = request.data.get("name", profile.name)
    new_email = request.data.get("email", profile.email)

    # Check for name conflict
    if UserProfile.objects.exclude(auth0_id=auth0_id).filter(name=new_name).exists():
        return Response({"error": "Name already taken."}, status=409)

    profile.name = new_name
    profile.email = new_email
    profile.save()

    return Response({"message": "Profile updated"})
