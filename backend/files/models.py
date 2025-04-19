from django.db import models
import uuid
import os
from django.db.models import Q
from django.utils import timezone

def file_upload_path(instance, filename):
    """Generate file path for new file upload"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('uploads', filename)

class File(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to=file_upload_path)
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=100)
    size = models.BigIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_hash = models.CharField(max_length=64, unique=True, null=True, blank=True)  # For deduplication
    is_duplicate = models.BooleanField(default=False)
    original_file = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='duplicates')
    storage_saved = models.BigIntegerField(default=0)  # Bytes saved through deduplication
    
    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['file_type']),
            models.Index(fields=['size']),
            models.Index(fields=['uploaded_at']),
            models.Index(fields=['file_hash']),
        ]
    
    def __str__(self):
        return self.original_filename

    @classmethod
    def search_files(cls, query=None, file_type=None, min_size=None, max_size=None, start_date=None, end_date=None):
        """
        Search and filter files based on multiple criteria
        """
        queryset = cls.objects.all()
        
        if query:
            queryset = queryset.filter(original_filename__icontains=query)
        
        if file_type:
            queryset = queryset.filter(file_type__icontains=file_type)
        
        if min_size is not None:
            queryset = queryset.filter(size__gte=min_size)
        
        if max_size is not None:
            queryset = queryset.filter(size__lte=max_size)
        
        if start_date:
            queryset = queryset.filter(uploaded_at__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(uploaded_at__lte=end_date)
        
        return queryset
