from django.db import models
import os
import uuid
from django.conf import settings

class UserSession(models.Model):
    # This model represents a user's editing session.
    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.session_id)

class Image(models.Model):
    # This model represents the uploaded images and their versions.
    session = models.ForeignKey(UserSession, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='uploads/')
    version = models.IntegerField(default=0) # 0 for original, increments with each edit
    created_at = models.DateTimeField(auto_now_add=True)
    is_original = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.session.session_id} - Version {self.version}"

    class Meta:
        ordering = ['created_at']

    def get_absolute_url(self):
        return self.image.url

    def save(self, *args, **kwargs):
        # If this is the first image being saved for the session, mark it as original.
        if self.version == 0:
            self.is_original = True
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.image:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)
        super(Image, self).delete(*args, **kwargs)
        
    def get_absolute_url(self):
        return f"{settings.MEDIA_URL}{self.image}"
    
