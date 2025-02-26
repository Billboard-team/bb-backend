from django.http import HttpResponse
from django.http import JsonResponse
from .models import Bill

# Create your views here.
def index(req):
    return HttpResponse(b'Test test')

def trending_bills(request):
    bills = Bill.objects.order_by('-actions_date')[:10]  
    data = [
        {
            "bill_id": bill.id,
            "title": bill.title,
            "action": bill.actions,
            "action_date": bill.actions_date,
            "description": bill.description,
            "congress": bill.congress,
            "bill_type": bill.bill_type,
            "bill_number": bill.bill_number,
            "summary": bill.summary.content if bill.summary else None,
            "text": bill.text.content if bill.text else None,
        }
        for bill in bills
    ]
    return JsonResponse({"trending_bills": data})

def recommended_bills(request):
    recommended = Bill.objects.order_by('-bill_type')[:5]  # Get the latest 5 bills

    data = [
        {
            "bill_id": bill.id,
            "title": bill.title,
            "action": bill.actions,
            "action_date": bill.actions_date,
            "description": bill.description,
            "congress": bill.congress,
            "bill_type": bill.bill_type,
            "bill_number": bill.bill_number,
            "summary": bill.summary.content if bill.summary else None,
            "text": bill.text.content if bill.text else None,
        }
        for bill in recommended
    ]
    
    return JsonResponse({"recommended_bills": data})

def single_bill(request, id):
    try:
        bill = Bill.objects.get(id=id)
        data = {
            "bill_id": bill.id,
            "title": bill.title,
            "action": bill.actions,
            "action_date": bill.actions_date,
            "description": bill.description,
            "congress": bill.congress,
            "bill_type": bill.bill_type,
            "bill_number": bill.bill_number,
            "summary": bill.summary.content if bill.summary else None,
            "text": bill.text.content if bill.text else None,
        }
        return JsonResponse({"bill": data})
    except Bill.DoesNotExist:
        return JsonResponse({"error": "Bill not found"}, status=404)