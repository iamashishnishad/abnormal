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
import logging
import mimetypes
import os

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 10485760  # 10MB in bytes

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
        file_obj.seek(0)
        for chunk in file_obj.chunks():
            sha256_hash.update(chunk)
        file_hash = sha256_hash.hexdigest()
        file_obj.seek(0)
        return file_hash

    @action(detail=False, methods=['post'])
    def check_duplicate(self, request):
        file_obj = request.FILES.get('file')
        if not file_obj:
            logger.error("No file provided in check_duplicate")
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        if file_obj.size is None or file_obj.size < 0:
            logger.error(f"Invalid file size in check_duplicate: {file_obj.size}")
            return Response({'error': 'Invalid file size'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            logger.info(f"Checking duplicate for file: {file_obj.name}, size: {file_obj.size}")
            file_hash = self._calculate_file_hash(file_obj)
            existing_file = File.objects.filter(file_hash=file_hash).first()
            
            if existing_file:
                logger.info(f"Duplicate found: {existing_file.original_filename}")
                return Response({
                    'is_duplicate': True,
                    'original_file_name': existing_file.original_filename,
                    'original_file_id': str(existing_file.id),
                    'file_hash': file_hash
                })
            
            logger.info("No duplicate found")
            return Response({
                'is_duplicate': False,
                'file_hash': file_hash
            })
        except Exception as e:
            logger.error(f"Error in check_duplicate: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request, *args, **kwargs):
        logger.info("Starting file upload")
        file_obj = request.FILES.get('file')
        if not file_obj:
            logger.error("No file provided")
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        if file_obj.size is None or file_obj.size < 0:
            logger.error(f"Invalid file size: {file_obj.size}")
            return Response({'error': 'Invalid file size'}, status=status.HTTP_400_BAD_REQUEST)
        
        if file_obj.size == 0:
            logger.error("Empty file uploaded")
            return Response({'error': 'Empty file not allowed'}, status=status.HTTP_400_BAD_REQUEST)
        
        if file_obj.size > MAX_FILE_SIZE:
            logger.error(f"File size exceeds maximum limit: {file_obj.size} bytes")
            return Response({'error': 'File size exceeds maximum limit'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            logger.info(f"Processing file: {file_obj.name}, size: {file_obj.size}")
            file_hash = self._calculate_file_hash(file_obj)
            
            # Check for existing file with the same hash
            existing_file = File.objects.filter(file_hash=file_hash).first()
            
            # Set file_type with fallback to mimetypes
            file_type = file_obj.content_type
            if not file_type or file_type == '':
                file_type, _ = mimetypes.guess_type(file_obj.name)
                file_type = file_type or 'application/octet-stream'
                logger.info(f"Set file_type from mimetypes: {file_type}")
            
            # Prepare data for serializer
            data = {
                'file': file_obj,
                'original_filename': file_obj.name,
                'file_type': file_type,
                'size': file_obj.size,
                'file_hash': file_hash,
                'is_duplicate': bool(existing_file),
                'duplicate_count': 0,
                'storage_saved': file_obj.size if existing_file else 0,
                'uploaded_at': timezone.now()
            }
            
            if existing_file:
                # For duplicates, reference the original file
                data['original_file'] = existing_file.id
                data['file'] = existing_file.file  # Reference original file's storage
            
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            headers = self.get_success_headers(serializer.data)
            logger.info(f"File uploaded successfully: {file_obj.name}, is_duplicate: {data['is_duplicate']}")
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', None)
        file_type = request.query_params.get('file_type', None)
        min_size = request.query_params.get('min_size', None)
        max_size = request.query_params.get('max_size', None)
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)

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




# from django.shortcuts import render
# from rest_framework import viewsets, status, filters
# from rest_framework.response import Response
# from rest_framework.decorators import action
# from django_filters.rest_framework import DjangoFilterBackend
# from .models import File
# from .serializers import FileSerializer
# import hashlib
# from datetime import datetime
# from django.utils import timezone
# import logging
# import mimetypes
# import os

# # Configure logging
# logger = logging.getLogger(__name__)

# # Maximum file size (10MB)
# MAX_FILE_SIZE = 10485760  # 10MB in bytes

# class FileViewSet(viewsets.ModelViewSet):
#     queryset = File.objects.all()
#     serializer_class = FileSerializer
#     filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
#     filterset_fields = ['file_type', 'is_duplicate']
#     search_fields = ['original_filename']
#     ordering_fields = ['size', 'uploaded_at', 'original_filename']

#     def _calculate_file_hash(self, file_obj):
#         """Calculate SHA-256 hash of the file content"""
#         sha256_hash = hashlib.sha256()
#         file_obj.seek(0)  # Ensure the file pointer is at the start
#         for chunk in file_obj.chunks():
#             sha256_hash.update(chunk)
#         file_hash = sha256_hash.hexdigest()
#         file_obj.seek(0)  # Reset file pointer
#         return file_hash

#     @action(detail=False, methods=['post'])
#     def check_duplicate(self, request):
#         """Check if a file is a duplicate before uploading"""
#         file_obj = request.FILES.get('file')
#         if not file_obj:
#             logger.error("No file provided in check_duplicate")
#             return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
#         if file_obj.size is None or file_obj.size < 0:
#             logger.error(f"Invalid file size in check_duplicate: {file_obj.size}")
#             return Response({'error': 'Invalid file size'}, status=status.HTTP_400_BAD_REQUEST)
        
#         try:
#             logger.info(f"Checking duplicate for file: {file_obj.name}, size: {file_obj.size}")
#             # Calculate file hash directly from chunks
#             file_hash = self._calculate_file_hash(file_obj)
            
#             # Check for duplicates
#             existing_file = File.objects.filter(file_hash=file_hash).first()
            
#             if existing_file:
#                 logger.info(f"Duplicate found: {existing_file.original_filename}")
#                 return Response({
#                     'is_duplicate': True,
#                     'original_file_name': existing_file.original_filename,
#                     'original_file_id': str(existing_file.id),
#                     'file_hash': file_hash
#                 })
            
#             logger.info("No duplicate found")
#             return Response({
#                 'is_duplicate': False,
#                 'file_hash': file_hash
#             })
#         except Exception as e:
#             logger.error(f"Error in check_duplicate: {str(e)}")
#             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     def create(self, request, *args, **kwargs):
#         """Upload a new file and handle deduplication"""
#         logger.info("Starting file upload")
#         file_obj = request.FILES.get('file')
#         if not file_obj:
#             logger.error("No file provided")
#             return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
#         if file_obj.size is None or file_obj.size < 0:
#             logger.error(f"Invalid file size: {file_obj.size}")
#             return Response({'error': 'Invalid file size'}, status=status.HTTP_400_BAD_REQUEST)
        
#         if file_obj.size == 0:
#             logger.error("Empty file uploaded")
#             return Response({'error': 'Empty file not allowed'}, status=status.HTTP_400_BAD_REQUEST)
        
#         if file_obj.size > MAX_FILE_SIZE:
#             logger.error(f"File size exceeds maximum limit: {file_obj.size} bytes")
#             return Response({'error': 'File size exceeds maximum limit'}, status=status.HTTP_400_BAD_REQUEST)
        
#         try:
#             logger.info(f"Processing file: {file_obj.name}, size: {file_obj.size}")
#             # Calculate file hash
#             file_hash = self._calculate_file_hash(file_obj)
            
#             # Set file_type with fallback to mimetypes
#             file_type = file_obj.content_type
#             if not file_type or file_type == '':
#                 file_type, _ = mimetypes.guess_type(file_obj.name)
#                 file_type = file_type or 'application/octet-stream'
#                 logger.info(f"Set file_type from mimetypes: {file_type}")
            
#             # Prepare data for serializer
#             data = {
#                 'file': file_obj,
#                 'original_filename': file_obj.name,
#                 'file_type': file_type,
#                 'size': file_obj.size,
#                 'file_hash': file_hash,
#                 'is_duplicate': False,
#                 'duplicate_count': 0,
#                 'storage_saved': 0,
#                 'uploaded_at': timezone.now()
#             }
            
#             serializer = self.get_serializer(data=data)
#             serializer.is_valid(raise_exception=True)
#             self.perform_create(serializer)
            
#             headers = self.get_success_headers(serializer.data)
#             logger.info(f"File uploaded successfully: {file_obj.name}")
#             return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
#         except Exception as e:
#             logger.error(f"Error processing file: {str(e)}")
#             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     @action(detail=False, methods=['get'])
#     def search(self, request):
#         """Advanced search endpoint"""
#         query = request.query_params.get('q', None)
#         file_type = request.query_params.get('file_type', None)
#         min_size = request.query_params.get('min_size', None)
#         max_size = request.query_params.get('max_size', None)
#         start_date = request.query_params.get('start_date', None)
#         end_date = request.query_params.get('end_date', None)

#         # Convert size parameters to integers if provided
#         if min_size is not None:
#             try:
#                 min_size = int(min_size)
#             except ValueError:
#                 return Response({'error': 'Invalid min_size parameter'}, status=status.HTTP_400_BAD_REQUEST)
        
#         if max_size is not None:
#             try:
#                 max_size = int(max_size)
#             except ValueError:
#                 return Response({'error': 'Invalid max_size parameter'}, status=status.HTTP_400_BAD_REQUEST)

#         # Convert date parameters to datetime objects if provided
#         if start_date:
#             try:
#                 start_date = timezone.make_aware(datetime.strptime(start_date, '%Y-%m-%d'))
#             except ValueError:
#                 return Response({'error': 'Invalid start_date format. Use YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)
        
#         if end_date:
#             try:
#                 end_date = timezone.make_aware(datetime.strptime(end_date, '%Y-%m-%d'))
#             except ValueError:
#                 return Response({'error': 'Invalid end_date format. Use YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)

#         queryset = File.search_files(
#             query=query,
#             file_type=file_type,
#             min_size=min_size,
#             max_size=max_size,
#             start_date=start_date,
#             end_date=end_date
#         )
        
#         page = self.paginate_queryset(queryset)
#         if page is not None:
#             serializer = self.get_serializer(page, many=True)
#             return self.get_paginated_response(serializer.data)

#         serializer = self.get_serializer(queryset, many=True)
#         return Response(serializer.data)

#     @action(detail=False, methods=['get'])
#     def storage_stats(self, request):
#         """Get storage statistics"""
#         total_files = File.objects.count()
#         total_size = sum(file.size for file in File.objects.all())
#         total_storage_saved = sum(file.storage_saved for file in File.objects.all())
#         duplicate_count = File.objects.filter(is_duplicate=True).count()
        
#         return Response({
#             'total_files': total_files,
#             'total_size': total_size,
#             'total_storage_saved': total_storage_saved,
#             'duplicate_count': duplicate_count,
#             'storage_efficiency': f"{((total_storage_saved / total_size) * 100):.2f}%" if total_size > 0 else "0%"
#         })


