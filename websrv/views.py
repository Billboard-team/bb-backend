from django.db.models import Q
from django.http import HttpResponse
from django.http import JsonResponse
from websrv.utils.congress import fetch_text_htm, fetch_text_sources
from websrv.utils.llm import Summarizer
from .models import Bill, Comment
from .serializers import CommentSerializer
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

def index(request):
    return JsonResponse({"message": "Welcome to BillBoard API"})

def trending_bills(request):
    search = request.GET.get("categories")
    
    bill = None
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
            "description": bill.description,
            "congress": bill.congress,
            "bill_type": bill.bill_type,
            "bill_number": bill.bill_number,
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
            "description": bill.description,
            "congress": bill.congress,
            "bill_type": bill.bill_type,
            "bill_number": bill.bill_number,
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

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    def get_queryset(self):
        # Filter comments by bill_id if provided
        bill_id = self.request.query_params.get('bill_id', None)
        if bill_id is not None:
            return Comment.objects.filter(bill_id=bill_id)
        return Comment.objects.all()

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        comment = self.get_object()
        comment.likes += 1
        comment.save()
        return Response({'status': 'success'})

    @action(detail=True, methods=['post'])
    def dislike(self, request, pk=None):
        comment = self.get_object()
        comment.dislikes += 1
        comment.save()
        return Response({'status': 'success'})

    def update(self, request, *args, **kwargs):
        comment = self.get_object()
        password = request.data.get('password')
        
        if not password or password != comment.password:
            return Response(
                {'error': 'Invalid password'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        password = request.data.get('password')
        
        if not password or password != comment.password:
            return Response(
                {'error': 'Invalid password'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)

@csrf_exempt
@require_http_methods(["GET"])
def get_bill_comments(request, bill_id):
    print(f"Fetching comments for bill {bill_id}")
    try:
        # Verify bill exists
        bill = Bill.objects.get(id=bill_id)
        comments = Comment.objects.filter(bill=bill).order_by('-created_at')
        return JsonResponse([{
            'id': comment.id,
            'text': comment.text,
            'user_name': comment.user_name,
            'likes': comment.likes,
            'dislikes': comment.dislikes,
            'created_at': comment.created_at.isoformat(),
            'updated_at': comment.updated_at.isoformat()
        } for comment in comments], safe=False)
    except Bill.DoesNotExist:
        return JsonResponse({'error': 'Bill not found'}, status=404)
    except Exception as e:
        print(f"Error fetching comments: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def add_bill_comment(request, bill_id):
    print(f"Adding comment for bill {bill_id}")
    print(f"Request body: {request.body.decode()}")
    try:
        # Verify bill exists
        bill = Bill.objects.get(id=bill_id)
        data = json.loads(request.body)
        comment = Comment.objects.create(
            bill=bill,
            text=data['text'],
            user_name=data.get('user_name', 'Guest'),
            password=data['password']
        )
        return JsonResponse({
            'id': comment.id,
            'text': comment.text,
            'user_name': comment.user_name,
            'likes': comment.likes,
            'dislikes': comment.dislikes,
            'created_at': comment.created_at.isoformat(),
            'updated_at': comment.updated_at.isoformat()
        })
    except Bill.DoesNotExist:
        return JsonResponse({'error': 'Bill not found'}, status=404)
    except KeyError as e:
        return JsonResponse({'error': f'Missing required field: {str(e)}'}, status=400)
    except Exception as e:
        print(f"Error adding comment: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["PUT", "DELETE"])
def manage_comment(request, bill_id, comment_id):
    print(f"Managing comment {comment_id} for bill {bill_id}")
    print(f"Method: {request.method}")
    print(f"Request body: {request.body.decode()}")
    
    try:
        comment = Comment.objects.get(id=comment_id, bill_id=bill_id)
        data = json.loads(request.body)
        
        # Verify password
        if not comment.password == data.get('password'):
            print("Password verification failed")
            return JsonResponse({'error': 'Invalid password'}, status=403)
            
        if request.method == "DELETE":
            print("Deleting comment")
            comment.delete()
            return JsonResponse({'message': 'Comment deleted successfully'})
            
        if request.method == "PUT":
            print("Updating comment")
            comment.text = data['text']
            comment.save()
            return JsonResponse({
                'id': comment.id,
                'text': comment.text,
                'user_name': comment.user_name,
                'likes': comment.likes,
                'dislikes': comment.dislikes,
                'created_at': comment.created_at.isoformat(),
                'updated_at': comment.updated_at.isoformat()
            })
            
    except Comment.DoesNotExist:
        print(f"Comment {comment_id} not found")
        return JsonResponse({'error': 'Comment not found'}, status=404)
    except KeyError as e:
        print(f"Missing required field: {str(e)}")
        return JsonResponse({'error': f'Missing required field: {str(e)}'}, status=400)
    except Exception as e:
        print(f"Error managing comment: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def like_comment(request, bill_id, comment_id):
    try:
        comment = Comment.objects.get(id=comment_id, bill_id=bill_id)
        comment.likes += 1
        comment.save()
        return JsonResponse({
            'id': comment.id,
            'likes': comment.likes,
            'dislikes': comment.dislikes
        })
    except Comment.DoesNotExist:
        return JsonResponse({'error': 'Comment not found'}, status=404)

@csrf_exempt
@require_http_methods(["POST"])
def dislike_comment(request, bill_id, comment_id):
    try:
        comment = Comment.objects.get(id=comment_id, bill_id=bill_id)
        comment.dislikes += 1
        comment.save()
        return JsonResponse({
            'id': comment.id,
            'likes': comment.likes,
            'dislikes': comment.dislikes
        })
    except Comment.DoesNotExist:
        return JsonResponse({'error': 'Comment not found'}, status=404)
