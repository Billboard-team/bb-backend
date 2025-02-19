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
            "description": bill.description
        }
        for bill in bills
    ]
    return JsonResponse({"trending_bills": data})

def recommended_bills(request):
    recommended = Bill.objects.order_by('-actions_date')[:5]  # Get the latest 5 bills

    data = [
        {
            "bill_id": bill.id,
            "title": bill.title,
            "action": bill.actions,
            "action_date": bill.actions_date,
            "description": bill.description
        }
        for bill in recommended
    ]
    
    return JsonResponse({"recommended_bills": data})
