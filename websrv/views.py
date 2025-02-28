from django.http import HttpResponse
from django.http import JsonResponse
from websrv.utils.congress import fetch_text_htm, fetch_text_sources
from websrv.utils.llm import Summarizer
from .models import Bill

def index(request):
    return JsonResponse({"message": "Welcome to BillBoard API"})

def trending_bills(request):
    bills = Bill.objects.order_by('-actions_date')[:10]  
    data = [
        {
            "bill_id": bill.pk,
            "title": bill.title,
            "action": bill.actions,
            "action_date": bill.actions_date,
            "description": bill.description
        }
        for bill in bills 
    ]
    return JsonResponse({"trending_bills": data})

#example of categorical requests, will change in future, right now it just
def trending_bills_education(request):
    bills = Bill.objects.filter(title__icontains="education").order_by('-actions_date')[:10]
    unique_titles = set()
    filtered_bills = []

    for bill in bills:
        if bill.title not in unique_titles:
            unique_titles.add(bill.title)
            filtered_bills.append(bill)


    data = [
        {
            "bill_id": bill.pk,
            "title": bill.title,
            "action": bill.actions,
            "action_date": bill.actions_date,
            "description": bill.description
        }
        for bill in filtered_bills[:10]
        
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
            "description": bill.description
        }
        for bill in recommended
    ]
    
    return JsonResponse({"recommended_bills": data})

def single_bill(request, id):
    try:
        bill = Bill.objects.get(id=id)
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
        }
        return JsonResponse({"bill": data})
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
