from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from .models import File
from .serializers import FileSerializer
import hashlib
from datetime import datetime
from django.utils import timezone

# Create your views here.

class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['file_type', 'is_duplicate']
    search_fields = ['original_filename']
    ordering_fields = ['size', 'uploaded_at', 'original_filename']

    def _calculate_file_hash(self, file_obj):
        """Calculate SHA-256 hash of the file content"""
        sha256_hash = hashlib.sha256()
        for chunk in file_obj.chunks():
            sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    @action(detail=False, methods=['post'])
    def check_duplicate(self, request):
        """Check if a file is a duplicate before uploading"""
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate file hash
        file_hash = self._calculate_file_hash(file_obj)
        
        # Check for duplicates
        existing_file = File.objects.filter(file_hash=file_hash).first()
        
        if existing_file:
            return Response({
                'is_duplicate': True,
                'original_file_name': existing_file.original_filename,
                'original_file_id': str(existing_file.id)
            })
        
        return Response({
            'is_duplicate': False
        })

    def create(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate file hash
        file_hash = self._calculate_file_hash(file_obj)
        
        # Check for duplicates
        existing_file = File.objects.filter(file_hash=file_hash).first()
        
        if existing_file:
            # Create a duplicate entry
            data = {
                'file': file_obj,
                'original_filename': file_obj.name,
                'file_type': file_obj.content_type,
                'size': file_obj.size,
                'file_hash': file_hash,
                'is_duplicate': True,
                'original_file': existing_file.id,
                'storage_saved': file_obj.size
            }
        else:
            # Create new file entry
            data = {
                'file': file_obj,
                'original_filename': file_obj.name,
                'file_type': file_obj.content_type,
                'size': file_obj.size,
                'file_hash': file_hash,
                'is_duplicate': False
            }
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced search endpoint"""
        query = request.query_params.get('q', None)
        file_type = request.query_params.get('file_type', None)
        min_size = request.query_params.get('min_size', None)
        max_size = request.query_params.get('max_size', None)
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)

        # Convert size parameters to integers if provided
        if min_size is not None:
            try:
                min_size = int(min_size)
            except ValueError:
                return Response({'error': 'Invalid min_size parameter'}, status=status.HTTP_400_BAD_REQUEST)
        
        if max_size is not None:
            try:
                max_size = int(max_size)
            except ValueError:
                return Response({'error': 'Invalid max_size parameter'}, status=status.HTTP_400_BAD_REQUEST)

        # Convert date parameters to datetime objects if provided
        if start_date:
            try:
                start_date = timezone.make_aware(datetime.strptime(start_date, '%Y-%m-%d'))
            except ValueError:
                return Response({'error': 'Invalid start_date format. Use YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)
        
        if end_date:
            try:
                end_date = timezone.make_aware(datetime.strptime(end_date, '%Y-%m-%d'))
            except ValueError:
                return Response({'error': 'Invalid end_date format. Use YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)

        queryset = File.search_files(
            query=query,
            file_type=file_type,
            min_size=min_size,
            max_size=max_size,
            start_date=start_date,
            end_date=end_date
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def storage_stats(self, request):
        """Get storage statistics"""
        total_files = File.objects.count()
        total_size = sum(file.size for file in File.objects.all())
        total_storage_saved = sum(file.storage_saved for file in File.objects.all())
        duplicate_count = File.objects.filter(is_duplicate=True).count()
        
        return Response({
            'total_files': total_files,
            'total_size': total_size,
            'total_storage_saved': total_storage_saved,
            'duplicate_count': duplicate_count,
            'storage_efficiency': f"{((total_storage_saved / total_size) * 100):.2f}%" if total_size > 0 else "0%"
        })
