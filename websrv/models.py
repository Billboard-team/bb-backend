from django.db import models

# Original Text
class Text(models.Model):
    content = models.TextField()

# Bill Summary
class Summary(models.Model):
    content = models.CharField(max_length=1000)

class AISummary(models.Model):
    content = models.TextField()

# Cosponsors / Congress Member
class Cosponsor(models.Model):
    bioguide_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100)
    full_name = models.CharField(max_length=255)
    party = models.CharField(max_length=10)
    state = models.CharField(max_length=5)
    district = models.IntegerField(null=True, blank=True)
    is_original_cosponsor = models.BooleanField()
    sponsorship_date = models.DateField()
    url = models.URLField()
    img_url = models.URLField(null=True)
    
# Bill
class Bill(models.Model):
    title = models.CharField(max_length=600)
    actions = models.CharField(max_length=400)
    description = models.CharField(max_length=400)
    actions_date = models.DateField("action date")
    congress = models.IntegerField(null=True)
    bill_type = models.CharField(max_length=5, null=True)
    bill_number = models.CharField(max_length=10, null=True)
    summary = models.ForeignKey(to=Summary, on_delete=models.CASCADE, null=True)
    text = models.ForeignKey(to=Text, on_delete=models.CASCADE, null=True)
    url = models.TextField(blank=True, null=True)
    cosponsors = models.ManyToManyField(Cosponsor, related_name="bills")

class User(models.Model):
    auth0_id = models.CharField(max_length=255, unique=True)  # Auth0 "sub"
    name = models.CharField(max_length=255)
    email = models.EmailField()
    avatar = models.URLField(blank=True)
    expertise_tags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name or self.email

class Comment(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    user_name = models.CharField(max_length=255)
    auth0_id = models.CharField(max_length=255)  # Store Auth0 user ID
    likes = models.IntegerField(default=0)
    dislikes = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']  # Newest first by default

# Track comment interactions for future uses plus prevent single user from spamming likes/dislikes
class CommentInteraction(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='interactions')
    auth0_id = models.CharField(max_length=255)  # Auth0 user ID
    interaction_type = models.CharField(max_length=10, choices=[('like', 'Like'), ('dislike', 'Dislike')])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['comment', 'auth0_id']  # One interaction per user per comment

# Track bill views for users
class BillView(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bill_views')
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='views')
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-viewed_at']  # Most recent first
        unique_together = ['user', 'bill']  # just one view per user per bill

    def __str__(self):
        return f"{self.user.name} viewed {self.bill.title}"

# Track bill likes for users
class BillLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='liker')
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='likee')
    timnestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timnestamp']  # Most recent first
        unique_together = ['user', 'bill']  # just one view per user per bill

    def __str__(self):
        return f"{self.user.name} viewed {self.bill.title}"
