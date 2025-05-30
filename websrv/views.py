from django.db.models import Q
from django.http import Http404, HttpResponse, JsonResponse
from websrv.utils.congress import fetch_cosponsors, fetch_text_htm, fetch_text_sources
from websrv.utils.llm import Summarizer
from websrv.utils.recommender import Recommender
from .models import Bill, BillLike, Cosponsor, BillView, Follow, User, Comment
import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import IntegrityError

def index(request):
    return JsonResponse({"message": "Welcome to BillBoard API"})

def trending_bills(request):
    search = request.GET.get("categories")
    
    if search:
        search_categories = search.split(",")
        search_categories = [s for s in search_categories if s]

        if not search_categories:
            bills = Bill.objects.order_by('-actions_date')[:10]  
        else:
            q = Q()
            for term in search_categories:
                q |= Q(title__icontains=term)
            bills = Bill.objects.filter(q).order_by('-actions_date')[:10]
    
    else:
        bills = Bill.objects.order_by('-actions_date')[:10]  

    data = [
        {
            "bill_id": bill.pk,
            "title": bill.title,
            "action": bill.actions,
            "action_date": bill.actions_date,
            "description": bill.description,
            "congress": bill.congress,
            "bill_type": bill.bill_type,
            "bill_number": bill.bill_number,
        }
        for bill in bills 
    ]
    return JsonResponse({"trending_bills": data})

def recommended_bills(request):
    recommended = Bill.objects.order_by('-actions_date')[:5]  # Get the latest 5 bills

    data = [
        {
            "bill_id": bill.pk,
            "title": bill.title,
            "action": bill.actions,
            "action_date": bill.actions_date,
            "description": bill.description,
            "congress": bill.congress,
            "bill_type": bill.bill_type,
            "bill_number": bill.bill_number,
        }
        for bill in recommended
    ]
    
    return JsonResponse({"recommended_bills": data})

def congress_members(request, congress):
    #fetch all cosponsors within provided congress
    members = Cosponsor.objects.order_by('last_name')

    data = [
        {
            "bioguide_id": c.bioguide_id,
            "full_name": c.full_name,
            "party": c.party,
            "state": c.state,
            "district": c.district,
            "image_url": c.img_url,
        }  for c in members  
    ]

    return JsonResponse({"congress_members": data})

def get_bill_detailed(request, id):
    try:
        bill = Bill.objects.get(id=id) 

        # Fetch cosponsor data
        cosponsor_data = Cosponsor.objects.filter(bills=bill)

        data = {
            "bill_id": bill.pk,
            "title": bill.title,
            "action": bill.actions,
            "action_date": bill.actions_date,
            "description": bill.description,
            "congress": bill.congress,
            "bill_type": bill.bill_type,
            "bill_number": bill.bill_number,
            "summary": bill.summary.content if bill.summary else None,
            "text": bill.text.content if bill.text else None,
            "url": bill.url,
            "cosponsors": [ {
                "bioguide_id": c.bioguide_id,
                "full_name": c.full_name,
                "fname" : c.first_name,
                "lname" : c.last_name,
                "party": c.party,
                "state": c.state,
                "district": c.district,
                "image_url": c.img_url,
                }  for c in cosponsor_data],
        }

        return JsonResponse({"bill": data})
    except Bill.DoesNotExist:
        return JsonResponse({"error": "Bill not found"}, status=404)

def get_member_data(request, bioguide_id):
    print("hit!")
    try:
        member = Cosponsor.objects.get(bioguide_id=bioguide_id)

        # Fetch cosponsor data
        bills = Bill.objects.filter(cosponsors=member)

        data = {
                "bioguide_id": member.bioguide_id,
                "full_name": member.full_name,
                "party": member.party,
                "state": member.state,
                "district": member.district,
                "image_url": member.img_url,
                "url": member.url,
                "cosponsored_bills" : [{
                    "bill_id": bill.pk,
                    "title": bill.title,
                    "action_date": bill.actions_date,
                    "action": bill.actions,
                    "bill_type": bill.bill_type,
                    "bill_number": bill.bill_number,
                    } for bill in bills
                ]
        }

        return JsonResponse({"cosponsor": data})
    except Bill.DoesNotExist:
        return JsonResponse({"error": "Bill not found"}, status=404)

def get_bill_text_original(request, id):
    try:
        bill = Bill.objects.get(id=id)
        summarizer = Summarizer()

        data = fetch_text_htm(bill.congress, bill.bill_type, bill.bill_number)
        if not data:
            return JsonResponse({"error": "Text not available"}, status=404)
        
        text_body = summarizer.clean_html(data)
        return JsonResponse({"text": text_body})
    except Bill.DoesNotExist:
        return JsonResponse({"error": "Bill not found"}, status=404)

def get_bill_text_summarized(request, id):
    try:
        bill = Bill.objects.get(id=id)
        summarizer = Summarizer()
        data = fetch_text_htm(bill.congress, bill.bill_type, bill.bill_number)
        if not data:
            return JsonResponse({"error": "Text not available"}, status=404)
        
        res = summarizer.summarize_html(data)
        return JsonResponse(res)
    except Bill.DoesNotExist:
        return JsonResponse({"error": "Bill not found"}, status=404)

def get_bill_text_sources(request, id):
    try:
        bill = Bill.objects.get(id=id)
        data = fetch_text_sources(bill.congress, bill.bill_type, bill.bill_number)
        if not data:
            return JsonResponse({"error": "Text not available"}, status=404)
        
        return JsonResponse(data)
    except Bill.DoesNotExist:
        return JsonResponse({"error": "Bill not found"}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def record_bill_view(request, id):
    try:
        bill = Bill.objects.get(id=id)
        auth0_id = request.user.sub
        user = User.objects.get(auth0_id=auth0_id)

        # Try to create a new view record
        try:
            BillView.objects.create(user=user, bill=bill)
        except IntegrityError:
            # If view record already exists, update the viewed_at timestamp
            view = BillView.objects.get(user=user, bill=bill)
            view.save()  # This will update the auto_now_add field

        return JsonResponse({"message": "Bill view recorded"})
    except Bill.DoesNotExist:
        return JsonResponse({"error": "Bill not found"}, status=404)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except Exception as e:
        logging.error(f"Error recording bill view: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_bill_view_history(request):
    try:
        auth0_id = request.user.sub
        user = User.objects.get(auth0_id=auth0_id)
        
        # Get all bill views for the user, ordered by most recent first
        bill_views = BillView.objects.filter(user=user)
        
        # Convert to list of dictionaries manually
        view_history = []
        for view in bill_views:
            view_history.append({
                'bill_id': view.bill.id,
                'bill_type': view.bill.bill_type,
                'congress': view.bill.congress,
                'bill_number': view.bill.bill_number,
                'title': view.bill.title,
                'viewed_at': view.viewed_at
            })
        
        return JsonResponse({"view_history": view_history})
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except Exception as e:
        logging.error(f"Error fetching bill view history: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_liked_bills(request):
    try:
        auth0_id = request.user.sub
        user = User.objects.get(auth0_id=auth0_id)
        
        # Get all bill views for the user, ordered by most recent first
        bill_views = BillLike.objects.filter(user=user)
        
        # Convert to list of dictionaries manually
        bills = []
        for view in bill_views:
            bills.append({
                'bill_id': view.bill.id,
                'bill_type': view.bill.bill_type,
                'congress': view.bill.congress,
                'bill_number': view.bill.bill_number,
                'title': view.bill.title,
                'liked_at': view.timnestamp,
            })
        
        return JsonResponse({"liked_bills": bills})
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except Exception as e:
        logging.error(f"Error fetching bill likes: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def like_bill(request, id):
    try:
        bill = Bill.objects.get(id=id)
        auth0_id = request.user.sub
        user = User.objects.get(auth0_id=auth0_id)

        BillLike.objects.create(user=user, bill=bill)
        return JsonResponse({"message": "Bill view recorded"})
    except Bill.DoesNotExist:
        return JsonResponse({"error": "Bill not found"}, status=404)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except Exception as e:
        logging.error(f"Error recording bill view: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def unlike_bill(request, id):
    try:
        bill = Bill.objects.get(id=id)
        auth0_id = request.user.sub
        user = User.objects.get(auth0_id=auth0_id)

        like_bill = BillLike.objects.get(bill=bill, user=user)
        like_bill.delete()

        return JsonResponse({"message": "Bill view recorded"})
    except Bill.DoesNotExist:
        return JsonResponse({"error": "Bill not found"}, status=404)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except BillLike.DoesNotExist:
        return JsonResponse({"error": "User have not liked the bill"}, status=404)
    except Exception as e:
        logging.error(f"Error unliking bill: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_if_liked_bill(request, id):
    try:
        auth0_id = request.user.sub
        user = User.objects.get(auth0_id=auth0_id)
        bill = Bill.objects.get(id=id)
        
        # Get all bill views for the user, ordered by most recent first
        BillLike.objects.get(user=user, bill=bill)
        return HttpResponse("OK")

    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except BillLike.DoesNotExist:
        return HttpResponse(status=404)
    except Exception as e:
        logging.error(f"Error fetching bill view history: {str(e)}")

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_activity_stats(request):
    try:
        auth0_id = request.user.sub
        user = User.objects.get(auth0_id=auth0_id)
        
        bill_views_count = BillView.objects.filter(user=user).count()
        comments_count = Comment.objects.filter(auth0_id=auth0_id).count()
        
        return JsonResponse({
            "bill_views": bill_views_count,
            "comments": comments_count
        })
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except Exception as e:
        logging.error(f"Error fetching user activity stats: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_specific_user_activity_stats(request, username):
    try:
        user = User.objects.get(name=username)
        
        bill_views_count = BillView.objects.filter(user=user).count()
        comments_count = Comment.objects.filter(auth0_id=user.auth0_id).count()
        
        return JsonResponse({
            "bill_views": bill_views_count,
            "comments": comments_count
        })
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except Exception as e:
        logging.error(f"Error fetching user activity stats: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def block_user(request, username):
    try:
        auth0_id = request.user.sub
        blocker = User.objects.get(auth0_id=auth0_id)
        blocked = User.objects.get(name=username)
        
        if blocker == blocked:
            return JsonResponse({"error": "Cannot block yourself"}, status=400)
            
        blocker.blocked_users.add(blocked)
        return JsonResponse({"message": f"Successfully blocked {username}"})
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except Exception as e:
        logging.error(f"Error blocking user: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def unblock_user(request, username):
    try:
        auth0_id = request.user.sub
        blocker = User.objects.get(auth0_id=auth0_id)
        blocked = User.objects.get(name=username)
        
        blocker.blocked_users.remove(blocked)
        return JsonResponse({"message": f"Successfully unblocked {username}"})
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except Exception as e:
        logging.error(f"Error unblocking user: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def is_user_blocked(request, username):
    try:
        auth0_id = request.user.sub
        blocker = User.objects.get(auth0_id=auth0_id)
        blocked = User.objects.get(name=username)
        
        is_blocked = blocker.blocked_users.filter(id=blocked.id).exists()
        return JsonResponse({"is_blocked": is_blocked})
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except Exception as e:
        logging.error(f"Error checking if user is blocked: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_blocked_users(request):
    try:
        auth0_id = request.user.sub
        user = User.objects.get(auth0_id=auth0_id)
        
        blocked_users = user.blocked_users.all()
        blocked_users_data = [{
            "name": user.name,
            "auth0_id": user.auth0_id
        } for user in blocked_users]
        
        return JsonResponse({"blocked_users": blocked_users_data})
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except Exception as e:
        logging.error(f"Error fetching blocked users: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recommended_bills(request):
    try:
        auth0_id = request.user.sub
        user = User.objects.get(auth0_id=auth0_id)
        recommender = Recommender()

        viewed_bills = BillView.objects.filter(user=user)

        for b in viewed_bills:
            recommender.fit_title(b.bill.title)

        words = recommender.get_candidate_words()
        print(words)

        q = Q()
        for term in words:
            q |= Q(title__icontains=term)
        bills = Bill.objects.filter(q).order_by('-actions_date')[:10]

        data = [
            {
                "bill_id": bill.pk,
                "title": bill.title,
                "action": bill.actions,
                "action_date": bill.actions_date,
                "description": bill.description,
                "congress": bill.congress,
                "bill_type": bill.bill_type,
                "bill_number": bill.bill_number,
            }
            for bill in bills 
        ]
        return JsonResponse({"bills": data})
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except Exception as e:
        logging.error(f"Error fetching recommendated bills: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_following_feed(request):

    try:
        user = User.objects.get(auth0_id=request.user.sub)
        following_users = Follow.objects.filter(follower_id=user.pk)
        data = []

        # get commented bills
        for u in following_users:
            cmt_qs = Comment.objects.filter(auth0_id=u.following.auth0_id)
            like_qs = BillLike.objects.filter(user=u.following)

            commented_bills = Bill.objects.filter(id__in=cmt_qs.values('bill_id')).distinct()
            liked_bills = Bill.objects.filter(id__in=like_qs.values('bill_id')).distinct()

            data.append({
                'username':u.following.name,
                'interaction': 'commented',
                'bills': [{
                    "bill_id": bill.pk,
                    "title": bill.title,
                    "action": bill.actions,
                    "action_date": bill.actions_date,
                    "description": bill.description,
                    "congress": bill.congress,
                    "bill_type": bill.bill_type,
                    "bill_number": bill.bill_number,
                } for bill in commented_bills] 
            })

            data.append({
                'username':u.following.name,
                'interaction': 'liked',
                'bills': [{
                    "bill_id": bill.pk,
                    "title": bill.title,
                    "action": bill.actions,
                    "action_date": bill.actions_date,
                    "description": bill.description,
                    "congress": bill.congress,
                    "bill_type": bill.bill_type,
                    "bill_number": bill.bill_number,
                } for bill in liked_bills] 
            })
        return JsonResponse({"followings": data})

    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except Follow.DoesNotExist:
        return JsonResponse({"error": "Follow not found"}, status=404)
    except Bill.DoesNotExist:
        return JsonResponse({"error": "Bill not found"}, status=404)
    except Exception as e:
        logging.error(f"Error fetching user activity stats: {str(e)}")
    pass
