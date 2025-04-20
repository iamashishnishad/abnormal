from rest_framework import serializers
from .models import File as FileModel
import logging
import hashlib
import os
from django.core.files import File as DjangoFile

logger = logging.getLogger(__name__)

class FileMetadataSerializer(serializers.Serializer):
    is_duplicate = serializers.BooleanField(default=False)
    file_hash = serializers.CharField(max_length=64, required=True)
    original_file_name = serializers.CharField(max_length=255, required=False, allow_null=True)
    original_file_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, attrs):
        if attrs.get('is_duplicate'):
            if not attrs.get('original_file_name') or not attrs.get('original_file_id'):
                raise serializers.ValidationError(
                    "original_file_name and original_file_id are required for duplicate files"
                )
        return attrs

class FileSerializer(serializers.ModelSerializer):
    metadata = FileMetadataSerializer(write_only=True)
    original_file_name = serializers.SerializerMethodField()
    storage_saved_human = serializers.SerializerMethodField()
    size_human = serializers.SerializerMethodField()

    class Meta:
        model = FileModel
        fields = [
            'id', 'file', 'original_filename', 'file_type', 'size', 
            'uploaded_at', 'file_hash', 'is_duplicate', 'original_file',
            'storage_saved', 'duplicate_count', 'original_file_name',
            'storage_saved_human', 'size_human', 'metadata'
        ]
        read_only_fields = [
            'id', 'file_type', 'size', 'uploaded_at', 'file_hash',
            'is_duplicate', 'original_file', 'storage_saved',
            'duplicate_count', 'storage_saved_human', 'size_human',
            'original_file_name'
        ]

    def get_original_file_name(self, obj):
        if obj.original_file:
            return obj.original_file.original_filename
        return None

    def get_storage_saved_human(self, obj):
        return self._humanize_size(obj.storage_saved)

    def get_size_human(self, obj):
        return self._humanize_size(obj.size)

    def _humanize_size(self, size):
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"

    def validate_file(self, value):
        """Validate file size and presence"""
        if not value:
            raise serializers.ValidationError("No file provided")
        if value.size is None or value.size < 0:
            raise serializers.ValidationError("Invalid file size")
        if value.size == 0:
            raise serializers.ValidationError("Empty file not allowed")
        if value.size > 10485760:  # 10MB
            raise serializers.ValidationError("File size exceeds maximum limit (10MB)")
        return value

    def validate(self, attrs):
        """Additional validation for deduplication"""
        if 'file' in attrs:
            # Ensure size is set if not provided
            if 'size' not in attrs or attrs['size'] is None:
                attrs['size'] = attrs['file'].size
                logger.info(f"Set size in serializer: {attrs['size']}")
        
        metadata = attrs.get('metadata')
        if metadata:
            # Validate file_hash against file content
            file_obj = attrs.get('file')
            if file_obj:
                file_obj.seek(0)
                sha256_hash = hashlib.sha256()
                for chunk in file_obj.chunks():
                    sha256_hash.update(chunk)
                calculated_hash = sha256_hash.hexdigest()
                file_obj.seek(0)
                
                if calculated_hash != metadata['file_hash']:
                    raise serializers.ValidationError(
                        "Provided file_hash does not match the file content"
                    )
        return attrs

    def create(self, validated_data):
        logger.info(f"Creating file with validated_data: {validated_data}")
        metadata = validated_data.pop('metadata', {})
        
        # Extract metadata fields
        is_duplicate = metadata.get('is_duplicate', False)
        file_hash = metadata.get('file_hash')
        original_file_id = metadata.get('original_file_id')
        
        validated_data['is_duplicate'] = is_duplicate
        
        if is_duplicate and original_file_id:
            try:
                original_file = FileModel.objects.get(id=original_file_id)
                validated_data['original_file'] = original_file
                validated_data['storage_saved'] = validated_data['file'].size
                validated_data['file'] = original_file.file  # Reuse the original file object
                # Do not set file_hash for duplicates to avoid UNIQUE constraint violation
            except FileModel.DoesNotExist:
                raise serializers.ValidationError("Original file not found")
        else:
            # Only set file_hash for non-duplicate files
            validated_data['file_hash'] = file_hash
        
        file_instance = FileModel.objects.create(**validated_data)
        
        # Update original file's duplicate count if duplicate
        if is_duplicate and original_file_id:
            original_file.duplicate_count = FileModel.objects.filter(original_file=original_file).count()
            original_file.save()
        
        return file_instance




