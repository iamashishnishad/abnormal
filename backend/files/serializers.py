from rest_framework import serializers
from .models import File

class FileSerializer(serializers.ModelSerializer):
    original_file_name = serializers.SerializerMethodField()
    storage_saved_human = serializers.SerializerMethodField()
    size_human = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = [
            'id', 'file', 'original_filename', 'file_type', 'size', 
            'uploaded_at', 'file_hash', 'is_duplicate', 'original_file',
            'storage_saved', 'original_file_name', 'storage_saved_human',
            'size_human'
        ]
        read_only_fields = ['id', 'uploaded_at', 'file_hash', 'is_duplicate', 
                          'original_file', 'storage_saved']

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