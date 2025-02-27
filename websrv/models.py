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

