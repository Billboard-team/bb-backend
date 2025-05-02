from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Bill, Follow, User, Cosponsor, Notification

from .serializers import UserProfileSerializer
from django.http import HttpResponse
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
import json
from django.conf import settings
import requests
import traceback
from rest_framework import status

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
    tags = ["Computer Science", "Engineering", "Political", "Art & Design", "Business", "Psychology", 
            "Media & Communication","Law", "Education", "History" ]
    return Response(tags)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_expertise_tags(request):
    from .models import User, Comment

    auth0_id = request.user.sub
    profile = User.objects.get(auth0_id=auth0_id)

    tags = request.data.get("tags", [])
    if not isinstance(tags, list):
        return Response({"error": "Tags must be a list."}, status=400)

    profile.expertise_tags = tags
    profile.save()
    Comment.objects.filter(auth0_id=auth0_id).update(expertise_tags=tags)
    return Response({"message": "Expertise tags updated."})   

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_profile_view2(request):
    auth0_id = request.user.sub
    profile = User.objects.get(auth0_id=auth0_id)

    new_name = request.data.get("name", profile.name)
    new_email = request.data.get("email", profile.email)

    # Check for name conflict
    if User.objects.exclude(auth0_id=auth0_id).filter(name=new_name).exists():
        return Response({"error": "Name already taken."}, status=409)

    profile.name = new_name
    profile.email = new_email
    profile.save()

    return Response({"message": "Profile updated"})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_profile_view(request, username):
    print("📥 Requested user profile:", username)
    try:
        user = User.objects.get(name=username)  # assuming `name` is the nickname/username
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)
    


@api_view(["POST", "DELETE"])
@permission_classes([IsAuthenticated])
def follow_user(request, username):

    auth0_id = request.user.sub
    follower = User.objects.get(auth0_id=auth0_id)
    following = User.objects.get(name=username)
    try:

        if request.method == "POST":
            Notification.objects.create(user=following, message=f"{follower.name} followed you.") #send notification       
            Follow.objects.get_or_create(follower=follower, following=following)
            return Response({"status": "followed"}, status=201)

        elif request.method == "DELETE":
            deleted, _ = Follow.objects.filter(follower=follower, following=following).delete()
            if deleted:
                return Response({"status": "unfollowed"}, status=204)
            else:
                return Response({"error": "Not following"}, status=404)

    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

@api_view(["POST", "DELETE"])
@permission_classes([IsAuthenticated])
def follow_rep(request, bioguide_id):
    #follow rep based on their bio guide id

    auth0_id = request.user.sub #JWT payload
    user, _ = User.objects.get_or_create(auth0_id=auth0_id)
    
    try:
        rep = Cosponsor.objects.get(bioguide_id=bioguide_id)
        #make exception for cosponsor nonexistence

        if request.method == "POST":
            user.followed_reps.add(rep)
            return Response({"status": "followed"}, status=201)
        
        elif request.method == "DELETE":
            deleted, _ = User.objects.filter(followed_reps=rep).delete()
            if deleted:
                return Response({"status": "unfollowed"}, status=204)
            else:
                return Response({"error": "Not following"}, status=404)
            
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_followed_bills(request):
    #fetch all bills that have been cosponsored by congress members that the user follows

    auth0_id = request.user.sub #JWT payload
    user, _ = User.objects.get_or_create(auth0_id=auth0_id)

    data = []

    try:
        followed_reps = User.objects.get(followed_reps)
        
        #this is not optimal searching but it will be ok for now
        for bill in Bill.objects.all(): # for all bills
            for rep in followed_reps: # for all followed reps
                if rep in bill.cosponsors.all(): # if rep exists within cosponsors
                    data.append(bill)
        return Response({"followed_bills": data}, status=200)

    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)


   


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def is_following_user(request, username):
    try:
        auth0_id = request.user.sub
        follower = User.objects.get(auth0_id=auth0_id)
        following = User.objects.get(name=username)

        is_following = Follow.objects.filter(follower=follower, following=following).exists()
        return Response({"is_following": is_following}, status=200)

    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_following(request):
    try:
        auth0_id = request.user.sub
        user = User.objects.get(auth0_id=auth0_id)
        following = Follow.objects.filter(follower=user).select_related('following')
        
        following_list = [{"id": f.following.id, "name": f.following.name} for f in following]
        
        return Response({"following": following_list})
    
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_followers(request):
    user = request.user
    followers = user.follower_set.all().select_related('follower')
    result = [{"id": f.follower.id, "name": f.follower.name} for f in followers]
    return Response({"followers": result})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def search_users(request):
    query = request.GET.get("q", "")
    users = User.objects.filter(name__icontains=query)[:10]
    data = [{"id": u.id, "name": u.name} for u in users]
    return Response({"results": data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_notifications(request):
    try:
        auth0_id = request.user.sub
        user = User.objects.get(auth0_id=auth0_id)
        notifications = Notification.objects.filter(user=user)

        data = [
            {
                "id": n.id,
                "message": n.message,
                "is_read": n.is_read,
                "created_at": n.created_at,
            }
            for n in notifications
        ]
        return Response({"notifications": data})
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, notification_id):
    try:
        auth0_id = request.user.sub
        user = User.objects.get(auth0_id=auth0_id)
        notification = Notification.objects.get(id=notification_id, user=user)
        notification.delete()
        return Response({"status": "deleted"})
    except Notification.DoesNotExist:
        return Response({"error": "Notification not found"}, status=404)
