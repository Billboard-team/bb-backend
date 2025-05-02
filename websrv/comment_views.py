from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from .models import Comment, Bill, CommentInteraction, User
import logging

logger = logging.getLogger(__name__)

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    permission_classes = [IsAuthenticated]  # Require authentication for all operations

    def get_queryset(self):
        try:
            queryset = Comment.objects.all()
            bill_id = self.request.query_params.get('bill_id', None)
            if bill_id is not None:
                # Verify bill exists
                Bill.objects.get(id=bill_id)
                queryset = queryset.filter(bill_id=bill_id)
                
                # Get the requesting user
                requesting_user = User.objects.get(auth0_id=self.request.user.sub)
                
                # Get all users that the requesting user has blocked
                blocked_users = requesting_user.blocked_users.all()
                
                # Filter out comments from users that the requesting user has blocked
                queryset = queryset.exclude(auth0_id__in=blocked_users.values_list('auth0_id', flat=True))
                
            return queryset
        except Bill.DoesNotExist:
            logger.error(f"Bill with id {bill_id} not found")
            raise PermissionDenied("Bill not found")
        except Exception as e:
            logger.error(f"Error in get_queryset: {str(e)}")
            raise

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            comments = []
            for comment in queryset:
                comments.append({
                    'id': comment.pk,
                    'bill': comment.bill.id,
                    'text': comment.text,
                    'user_name': comment.user_name,
                    'auth0_id': comment.auth0_id,
                    'likes': comment.likes,
                    'dislikes': comment.dislikes,
                    'created_at': comment.created_at,
                    'updated_at': comment.updated_at,
                    'expertise_tags': comment.expertise_tags
                })
            return Response(comments)
        except Exception as e:
            logger.error(f"Error in list: {str(e)}")
            raise

    def create(self, request):
        try:
            # Get bill_id from request data
            bill_id = request.data.get('bill')
            if not bill_id:
                raise PermissionDenied("Bill ID is required")
            
            # Verify bill exists
            bill = Bill.objects.get(id=bill_id)
            
            # Get user info from Auth0
            user = request.user
            auth0_id = user.sub
            user_name = request.data.get('user_name') or getattr(user, 'name', None) or getattr(user, 'email', None) or 'Anonymous'
            
            from .models import User  # make sure User is imported
            profile = User.objects.get(auth0_id=auth0_id)
            expertise_tags = profile.expertise_tags
            # Create the comment
            comment = Comment.objects.create(
                text=request.data.get('text'),
                user_name=user_name,
                auth0_id=auth0_id,
                expertise_tags=expertise_tags,
                bill=bill
            )
            
            # Return the created comment
            return Response({
                'id': comment.pk,
                'bill': comment.bill.id,
                'text': comment.text,
                'user_name': comment.user_name,
                'auth0_id': comment.auth0_id,
                'likes': comment.likes,
                'dislikes': comment.dislikes,
                'created_at': comment.created_at,
                'updated_at': comment.updated_at,
                'expertise_tags': comment.expertise_tags
            }, status=status.HTTP_201_CREATED)
            
        except Bill.DoesNotExist:
            logger.error("Bill not found")
            raise PermissionDenied("Bill not found")
        except Exception as e:
            logger.error(f"Error in create: {str(e)}")
            raise

    def update(self, request, pk=None):
        try:
            # Get the comment
            comment = self.get_object()
            
            # Check ownership
            if comment.auth0_id != request.user.sub:
                logger.error(f'Permission denied: User {request.user.sub} does not own comment {comment.id}')
                raise PermissionDenied("You can only edit your own comments")
            
            # Update the text
            new_text = request.data.get('text')
            if new_text is not None:
                comment.text = new_text
                comment.save()
                
                # Return the updated comment
                return Response({
                    'id': comment.id,
                    'bill': comment.bill.id,
                    'text': comment.text,
                    'user_name': comment.user_name,
                    'auth0_id': comment.auth0_id,
                    'likes': comment.likes,
                    'dislikes': comment.dislikes,
                    'created_at': comment.created_at,
                    'updated_at': comment.updated_at,
                    'expertise_tags': comment.expertise_tags
                })
            else:
                logger.error('No text provided in update request')
                return Response({'error': 'Text is required'}, status=400)
                
        except Exception as e:
            logger.error(f"Error in update: {str(e)}")
            raise

    def destroy(self, request, *args, **kwargs):
        try:
            comment = self.get_object()
            
            # Check ownership
            if comment.auth0_id != request.user.sub:
                logger.error(f'Permission denied: User {request.user.sub} does not own comment {comment.id}')
                raise PermissionDenied("You can only delete your own comments")
            
            comment.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error in destroy: {str(e)}")
            raise

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        try:
            comment = self.get_object()
            auth0_id = request.user.sub

            # Check if user has already interacted with this comment
            existing_interaction = CommentInteraction.objects.filter(
                comment=comment,
                auth0_id=auth0_id
            ).first()

            if existing_interaction:
                if existing_interaction.interaction_type == 'like':
                    # User is trying to like again, remove the like
                    existing_interaction.delete()
                    comment.likes -= 1
                else:
                    # User is switching from dislike to like
                    existing_interaction.interaction_type = 'like'
                    existing_interaction.save()
                    comment.dislikes -= 1
                    comment.likes += 1
            else:
                # New like
                CommentInteraction.objects.create(
                    comment=comment,
                    auth0_id=auth0_id,
                    interaction_type='like'
                )
                comment.likes += 1

            comment.save()
            
            return Response({
                'id': comment.id,
                'bill': comment.bill.id,
                'text': comment.text,
                'user_name': comment.user_name,
                'auth0_id': comment.auth0_id,
                'likes': comment.likes,
                'dislikes': comment.dislikes,
                'created_at': comment.created_at,
                'updated_at': comment.updated_at,
                'expertise_tags': comment.expertise_tags
            })
        except Exception as e:
            logger.error(f"Error in like action: {str(e)}")
            raise

    @action(detail=True, methods=['post'])
    def dislike(self, request, pk=None):
        try:
            comment = self.get_object()
            auth0_id = request.user.sub

            # Check if user has already interacted with this comment
            existing_interaction = CommentInteraction.objects.filter(
                comment=comment,
                auth0_id=auth0_id
            ).first()

            if existing_interaction:
                if existing_interaction.interaction_type == 'dislike':
                    # User is trying to dislike again, remove the dislike
                    existing_interaction.delete()
                    comment.dislikes -= 1
                else:
                    # User is switching from like to dislike
                    existing_interaction.interaction_type = 'dislike'
                    existing_interaction.save()
                    comment.likes -= 1
                    comment.dislikes += 1
            else:
                # New dislike
                CommentInteraction.objects.create(
                    comment=comment,
                    auth0_id=auth0_id,
                    interaction_type='dislike'
                )
                comment.dislikes += 1

            comment.save()
            
            return Response({
                'id': comment.id,
                'bill': comment.bill.id,
                'text': comment.text,
                'user_name': comment.user_name,
                'auth0_id': comment.auth0_id,
                'likes': comment.likes,
                'dislikes': comment.dislikes,
                'created_at': comment.created_at,
                'updated_at': comment.updated_at,
                'expertise_tags': comment.expertise_tags
            })
        except Exception as e:
            logger.error(f"Error in dislike action: {str(e)}")
            raise 
