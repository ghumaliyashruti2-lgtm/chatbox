from django.db import models
from django.contrib.auth.models import User
import uuid

class History(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    chat_id = models.UUIDField(default=uuid.uuid4, editable=False) 
    user_message = models.TextField()
    ai_message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_archived = models.BooleanField(default=False)

    uploaded_file = models.FileField(
        upload_to="chat_uploads/",
        null=True,
        blank=True
    )


