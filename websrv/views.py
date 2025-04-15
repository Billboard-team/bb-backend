from django.db.models import Q
from django.http import JsonResponse
from websrv.utils.congress import fetch_cosponsors, fetch_text_htm, fetch_text_sources
from websrv.utils.llm import Summarizer
from .models import Bill, Cosponsor

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

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_profile(request):
    user = request.user
    return Response({
        "id": user.id,
        "email": user.email,
        "username": user.username,
        # Add other fields if your User model has more
    })
