from rest_framework import serializers
from .models import File
import logging

logger = logging.getLogger(__name__)

class FileSerializer(serializers.ModelSerializer):
    original_file_name = serializers.SerializerMethodField()
    storage_saved_human = serializers.SerializerMethodField()
    size_human = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = [
            'id', 'file', 'original_filename', 'file_type', 'size', 
            'uploaded_at', 'file_hash', 'is_duplicate', 'original_file',
            'storage_saved', 'duplicate_count', 'original_file_name',
            'storage_saved_human', 'size_human'
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
        return attrs

    def create(self, validated_data):
        logger.info(f"Creating file with validated_data: {validated_data}")
        # Create the File instance, letting the model's save method handle deduplication
        return File.objects.create(**validated_data)



# from rest_framework import serializers
# from .models import File
# import logging

# logger = logging.getLogger(__name__)

# class FileSerializer(serializers.ModelSerializer):
#     original_file_name = serializers.SerializerMethodField()
#     storage_saved_human = serializers.SerializerMethodField()
#     size_human = serializers.SerializerMethodField()

#     class Meta:
#         model = File
#         fields = [
#             'id', 'file', 'original_filename', 'file_type', 'size', 
#             'uploaded_at', 'file_hash', 'is_duplicate', 'original_file',
#             'storage_saved', 'original_file_name', 'storage_saved_human',
#             'size_human'
#         ]
#         read_only_fields = [
#             'id', 'file_type', 'uploaded_at', 'storage_saved_human',
#             'size_human'
#         ]

#     def get_original_file_name(self, obj):
#         if obj.original_file:
#             return obj.original_file.original_filename
#         return None

#     def get_storage_saved_human(self, obj):
#         return self._humanize_size(obj.storage_saved)

#     def get_size_human(self, obj):
#         return self._humanize_size(obj.size)

#     def _humanize_size(self, size):
#         """Convert bytes to human readable format"""
#         for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
#             if size < 1024.0:
#                 return f"{size:.2f} {unit}"
#             size /= 1024.0
#         return f"{size:.2f} PB"

#     def create(self, validated_data):
#         logger.info(f"Creating file with validated_data: {validated_data}")
#         # Ensure size is set
#         if 'size' not in validated_data or validated_data['size'] is None:
#             file = validated_data.get('file')
#             if file:
#                 validated_data['size'] = file.size
#                 logger.info(f"Set size in serializer: {validated_data['size']}")
#             else:
#                 raise serializers.ValidationError("File size cannot be determined")
#         return super().create(validated_data)



