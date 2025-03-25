import uuid
from django.db import models

class License(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    identifier = models.CharField(max_length=100, blank=True, null=True)
    full_text = models.TextField(blank=True, null=True)
    scheme = models.CharField(max_length=100, blank=True, null=True)
    scheme_url = models.URLField(blank=True, null=True)
    url = models.URLField(blank=True, null=True)

    class Meta: ordering = ['identifier', 'name']
    def __str__(self): return self.identifier or self.name
