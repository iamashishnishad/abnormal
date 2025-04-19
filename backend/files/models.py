from django.db import models
import uuid
import os
import hashlib
from django.db.models import Q
from django.utils import timezone
import logging
from django.core.files import File

logger = logging.getLogger(__name__)

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
    duplicate_count = models.IntegerField(default=0)  # Number of duplicates of this file
    
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

    def calculate_file_hash(self):
        """Calculate SHA-256 hash of the file content"""
        if not self.file:
            return None
        
        sha256_hash = hashlib.sha256()
        try:
            with self.file.open('rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating file hash: {str(e)}")
            return None

    def save(self, *args, **kwargs):
        logger.info(f"Saving file: {self.original_filename}, size: {self.size}, file_hash: {self.file_hash}")
        # Only calculate file hash for new files if not provided
        if not self.pk and not self.file_hash and self.file:
            self.file_hash = self.calculate_file_hash()
            logger.info(f"Calculated file_hash: {self.file_hash}")
        
        # Ensure size is set
        if self.file and self.size is None:
            self.file.seek(0)
            self.size = self.file.size
            self.file.seek(0)  # Reset file pointer after reading size
            logger.info(f"Set size from file: {self.size}")
        
        # Check for duplicates if this is a new file and hash is set
        if not self.pk and self.file_hash:
            existing_file = File.objects.filter(file_hash=self.file_hash).first()
            if existing_file:
                logger.info(f"Duplicate found for {self.original_filename}: original is {existing_file.original_filename}")
                self.is_duplicate = True
                self.original_file = existing_file
                self.storage_saved = self.size
                # Reference the original file's storage
                self.file = File(existing_file.file, name=os.path.basename(existing_file.file.name))
                # Update the original file's duplicate count
                existing_file.duplicate_count = File.objects.filter(original_file=existing_file).count() + 1
                existing_file.save()
        
        super().save(*args, **kwargs)

    @property
    def original_file_name(self):
        return self.original_file.original_filename if self.original_file else None

    @property
    def storage_saved_human(self):
        return self._format_size(self.storage_saved)

    @property
    def size_human(self):
        return self._format_size(self.size)

    def _format_size(self, size):
        """Format size in bytes to human readable format"""
        if size < 1024:
            return f"{size} B"
        size /= 1024.0
        if size < 1024:
            return f"{size:.2f} KB"
        size /= 1024.0
        if size < 1024:
            return f"{size:.2f} MB"
        size /= 1024.0
        if size < 1024:
            return f"{size:.2f} GB"
        size /= 1024.0
        return f"{size:.2f} TB"

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


# from django.db import models
# import uuid
# import os
# import hashlib
# from django.db.models import Q
# from django.utils import timezone

# def file_upload_path(instance, filename):
#     """Generate file path for new file upload"""
#     ext = filename.split('.')[-1]
#     filename = f"{uuid.uuid4()}.{ext}"
#     return os.path.join('uploads', filename)

# class File(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     file = models.FileField(upload_to=file_upload_path)
#     original_filename = models.CharField(max_length=255)
#     file_type = models.CharField(max_length=100)
#     size = models.BigIntegerField()
#     uploaded_at = models.DateTimeField(auto_now_add=True)
#     file_hash = models.CharField(max_length=64, unique=True, null=True, blank=True)  # For deduplication
#     is_duplicate = models.BooleanField(default=False)
#     original_file = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='duplicates')
#     storage_saved = models.BigIntegerField(default=0)  # Bytes saved through deduplication
#     duplicate_count = models.IntegerField(default=0)  # Number of duplicates of this file
    
#     class Meta:
#         ordering = ['-uploaded_at']
#         indexes = [
#             models.Index(fields=['file_type']),
#             models.Index(fields=['size']),
#             models.Index(fields=['uploaded_at']),
#             models.Index(fields=['file_hash']),
#         ]
    
#     def __str__(self):
#         return self.original_filename

#     def calculate_file_hash(self):
#         """Calculate SHA-256 hash of the file content"""
#         if not self.file:
#             return None
        
#         sha256_hash = hashlib.sha256()
#         try:
#             with self.file.open('rb') as f:
#                 for chunk in iter(lambda: f.read(4096), b''):
#                     sha256_hash.update(chunk)
#             return sha256_hash.hexdigest()
#         except Exception:
#             return None

#     def save(self, *args, **kwargs):
#         # Only calculate file hash for new files if not provided
#         if not self.pk and not self.file_hash and self.file:
#             self.file_hash = self.calculate_file_hash()
        
#         # Ensure size is set
#         if self.file and self.size is None:
#             self.file.seek(0)
#             self.size = self.file.size
#             self.file.seek(0)  # Reset file pointer after reading size
        
#         super().save(*args, **kwargs)

#     @property
#     def original_file_name(self):
#         return self.original_file.original_filename if self.original_file else None

#     @property
#     def storage_saved_human(self):
#         return self._format_size(self.storage_saved)

#     @property
#     def size_human(self):
#         return self._format_size(self.size)

#     def _format_size(self, size):
#         """Format size in bytes to human readable format"""
#         if size < 1024:
#             return f"{size} B"
#         size /= 1024.0
#         if size < 1024:
#             return f"{size:.2f} KB"
#         size /= 1024.0
#         if size < 1024:
#             return f"{size:.2f} MB"
#         size /= 1024.0
#         if size < 1024:
#             return f"{size:.2f} GB"
#         size /= 1024.0
#         return f"{size:.2f} TB"

#     @classmethod
#     def search_files(cls, query=None, file_type=None, min_size=None, max_size=None, start_date=None, end_date=None):
#         """
#         Search and filter files based on multiple criteria
#         """
#         queryset = cls.objects.all()
        
#         if query:
#             queryset = queryset.filter(original_filename__icontains=query)
        
#         if file_type:
#             queryset = queryset.filter(file_type__icontains=file_type)
        
#         if min_size is not None:
#             queryset = queryset.filter(size__gte=min_size)
        
#         if max_size is not None:
#             queryset = queryset.filter(size__lte=max_size)
        
#         if start_date:
#             queryset = queryset.filter(uploaded_at__gte=start_date)
        
#         if end_date:
#             queryset = queryset.filter(uploaded_at__lte=end_date)
        
#         return queryset



# from django.db import models
# import uuid
# import os
# import hashlib
# from django.db.models import Q
# from django.utils import timezone

# def file_upload_path(instance, filename):
#     """Generate file path for new file upload"""
#     ext = filename.split('.')[-1]
#     filename = f"{uuid.uuid4()}.{ext}"
#     return os.path.join('uploads', filename)

# class File(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     file = models.FileField(upload_to=file_upload_path)
#     original_filename = models.CharField(max_length=255)
#     file_type = models.CharField(max_length=100)
#     size = models.BigIntegerField()
#     uploaded_at = models.DateTimeField(auto_now_add=True)
#     file_hash = models.CharField(max_length=64, unique=True, null=True, blank=True)  # For deduplication
#     is_duplicate = models.BooleanField(default=False)
#     original_file = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='duplicates')
#     storage_saved = models.BigIntegerField(default=0)  # Bytes saved through deduplication
#     duplicate_count = models.IntegerField(default=0)  # Number of duplicates of this file
    
#     class Meta:
#         ordering = ['-uploaded_at']
#         indexes = [
#             models.Index(fields=['file_type']),
#             models.Index(fields=['size']),
#             models.Index(fields=['uploaded_at']),
#             models.Index(fields=['file_hash']),
#         ]
    
#     def __str__(self):
#         return self.original_filename

#     def calculate_file_hash(self):
#         """Calculate SHA-256 hash of the file content"""
#         if not self.file:
#             return None
        
#         sha256_hash = hashlib.sha256()
#         try:
#             with self.file.open('rb') as f:
#                 for chunk in iter(lambda: f.read(4096), b''):
#                     sha256_hash.update(chunk)
#             return sha256_hash.hexdigest()
#         except Exception:
#             return None

#     def save(self, *args, **kwargs):
#         # Calculate file hash if not set
#         if not self.file_hash and self.file:
#             self.file_hash = self.calculate_file_hash()
        
#         # Check for duplicates if this is a new file
#         if not self.pk and self.file_hash:
#             existing_file = File.objects.filter(file_hash=self.file_hash).first()
#             if existing_file:
#                 self.is_duplicate = True
#                 self.original_file = existing_file
#                 self.storage_saved = self.size
#                 # Update the original file's duplicate count
#                 existing_file.duplicate_count = File.objects.filter(original_file=existing_file).count() + 1
#                 existing_file.save()
        
#         super().save(*args, **kwargs)

#     @property
#     def original_file_name(self):
#         return self.original_file.original_filename if self.original_file else None

#     @property
#     def storage_saved_human(self):
#         return self._format_size(self.storage_saved)

#     @property
#     def size_human(self):
#         return self._format_size(self.size)

#     def _format_size(self, size):
#         """Format size in bytes to human readable format"""
#         if size < 1024:
#             return f"{size} B"
#         size /= 1024.0
#         if size < 1024:
#             return f"{size:.2f} KB"
#         size /= 1024.0
#         if size < 1024:
#             return f"{size:.2f} MB"
#         size /= 1024.0
#         if size < 1024:
#             return f"{size:.2f} GB"
#         size /= 1024.0
#         return f"{size:.2f} TB"

#     @classmethod
#     def search_files(cls, query=None, file_type=None, min_size=None, max_size=None, start_date=None, end_date=None):
#         """
#         Search and filter files based on multiple criteria
#         """
#         queryset = cls.objects.all()
        
#         if query:
#             queryset = queryset.filter(original_filename__icontains=query)
        
#         if file_type:
#             queryset = queryset.filter(file_type__icontains=file_type)
        
#         if min_size is not None:
#             queryset = queryset.filter(size__gte=min_size)
        
#         if max_size is not None:
#             queryset = queryset.filter(size__lte=max_size)
        
#         if start_date:
#             queryset = queryset.filter(uploaded_at__gte=start_date)
        
#         if end_date:
#             queryset = queryset.filter(uploaded_at__lte=end_date)
        
#         return queryset
