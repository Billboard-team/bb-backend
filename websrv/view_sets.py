from websrv.models import Comment
from .serializers import CommentSerializer
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action

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
