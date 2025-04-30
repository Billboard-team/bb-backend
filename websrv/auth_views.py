from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import User
from .serializers import UserProfileSerializer
from django.http import HttpResponse
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
import json
from django.conf import settings
import requests


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    user = request.user  # 

    auth0_id = user.sub
    profile, created = User.objects.get_or_create(
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
    user = User.objects.get(auth0_id=auth0_id)

    nickname = request.data.get("name", "").strip()
    if not nickname:
        return Response({"error": "Name is required."}, status=400)

        # ✅ Check if another user already has this name
    if User.objects.filter(name=nickname).exclude(pk=user.pk).exists():
        return Response({"error": "Nickname already taken."}, status=409)
    
    user.name = nickname
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
                deleted, _ = User.objects.filter(auth0_id=auth0_id).delete()
                deleted_count += deleted

        return JsonResponse(
            {"status": "ok", "deleted_users": deleted_count},
            status=200,
        )

    except Exception as e:
        return JsonResponse(
            {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
        )

import traceback

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_account_view(request):
    print("🔥 DELETE ACCOUNT VIEW TRIGGERED")

    try:
        auth0_id = request.user.sub
        print("🔑 Auth0 ID:", getattr(request.user, "sub", "MISSING"))
        print(settings.AUTH0_DOMAIN)
        print(settings.AUTH0_CLIENT_ID)
        print(settings.AUTH0_CLIENT_SECRET)
        # Step 1: Get Management API token
        token_url = f"https://{settings.AUTH0_DOMAIN}/oauth/token"
        token_data = {
            "client_id": settings.AUTH0_CLIENT_ID,
            "client_secret": settings.AUTH0_CLIENT_SECRET,
            "audience": f"https://{settings.AUTH0_DOMAIN}/api/v2/",
            "grant_type": "client_credentials"
        }

        token_res = requests.post(token_url, json=token_data)
        print("🔐 TOKEN RES:", token_res.status_code, token_res.text)

        if token_res.status_code != 200:
            return Response({"error": "Failed to get management token"}, status=500)

        mgmt_token = token_res.json()["access_token"]

        # Step 2: Delete Auth0 user
        delete_url = f"https://{settings.AUTH0_DOMAIN}/api/v2/users/{auth0_id}"
        delete_res = requests.delete(
            delete_url,
            headers={"Authorization": f"Bearer {mgmt_token}"}
        )

        print("🧨 DELETE RES:", delete_res.status_code, delete_res.text)

        if delete_res.status_code != 204:
            return Response({"error": "Auth0 delete failed"}, status=delete_res.status_code)

        # Step 3: Delete local user profile
        from .models import User
        User.objects.filter(auth0_id=auth0_id).delete()

        return Response({"message": "User account deleted"})

    except Exception as e:
        print("❌ DELETE EXCEPTION:", str(e))
        traceback.print_exc()
        return Response({"error": str(e)}, status=500)

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

