from django.db import models

class Task(models.Model):
    title = models.CharField(max_length=120)
    done = models.BooleanField(default=False)
    class Meta:
        ordering = ["id"]
