from django.db import models

# Original Text
class Text(models.Model):
    content = models.TextField()

# Bill Summary
class Summary(models.Model):
    content = models.CharField(max_length=1000)

class AISummary(models.Model):
    content = models.TextField()

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
    user_name = models.CharField(max_length=255)  # Store as Guest if no user
    password = models.CharField(max_length=255)  # For editing/deleting
    likes = models.IntegerField(default=0)
    dislikes = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']  # Newest first by default