# file_storage_app/views.py

from rest_framework import generics, views
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Value, IntegerField
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from files.models import File, Organization, Download, User
from files.serializers import (
    FileUploadSerializer, 
    FileDetailSerializer, 
    OrganizationWithDownloadCountSerializer, 
    UserDownloadSerializer,
    FileDownloadSerializer,
)
from files.permissions import IsFileUploaderOrganization


class FileDownloadView(views.APIView):
    """
    GET /api/v1/files/<file_id>/download/
    """
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, file_id, format=None):
        file_object = get_object_or_404(File, pk=file_id)
        # In production this should be a background task (Celery, etc.).
        Download.objects.create(
            file=file_object,
            downloaded_by=request.user
        )
        try:
            response = FileResponse(
                file_object.file.open('rb'),
                content_type=file_object.content_type or 'application/octet-stream'
            )
            response['Content-Disposition'] = f'attachment; filename="{file_object.name}"'
            response['Content-Length'] = file_object.file_size
            return response
        except FileNotFoundError:
            return Response({"detail": "File not found on storage."}, status=404)


class FileListCreateView(generics.ListCreateAPIView):
    """
    GET, POST /api/v1/organizations/<org_id>/files/
    """
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated, IsFileUploaderOrganization]
    serializer_class = FileUploadSerializer
    
    def get_queryset(self):
        org_id = self.kwargs['org_id']
        return File.objects.filter(organization_id=org_id)
        
    def perform_create(self, serializer):
        org_id = self.kwargs['org_id']
        organization = get_object_or_404(Organization, id=org_id)
        uploaded_file = self.request.FILES.get('file')
        serializer.save(
            uploaded_by=self.request.user,
            organization=organization,
            file_size=uploaded_file.size if uploaded_file else None,
            content_type=uploaded_file.content_type if uploaded_file else None
        )


class GlobalFileListView(generics.ListAPIView):
    """
    GET /api/v1/files/
    TODO: There probably should be a pagination in all list views but not mentioned in the requirements.
    """
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = FileDetailSerializer
    
    def get_queryset(self):
        return File.objects.select_related('organization', 'uploaded_by').annotate(download_count=Count('downloads'))


class OrganizationListView(generics.ListAPIView):
    """
    GET /api/v1/organizations/
    """
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = OrganizationWithDownloadCountSerializer
    
    def get_queryset(self):
        return Organization.objects.annotate(
            total_downloads=Coalesce(
                Count('files__downloads__id'),
                Value(0),
                output_field=IntegerField()
            )
        )


class UserDownloadHistoryView(generics.ListAPIView):
    """
    GET /api/v1/users/<user_id>/downloads/
    """
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = UserDownloadSerializer

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        get_object_or_404(User, pk=user_id) 
        return Download.objects.filter(downloaded_by_id=user_id).select_related('file', 'file__organization')


class FileDownloadHistoryView(generics.ListAPIView):
    """
    GET /api/v1/files/<file_id>/downloads/
    """
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = FileDownloadSerializer

    def get_queryset(self):
        file_id = self.kwargs['file_id']
        get_object_or_404(File, pk=file_id)        
        return Download.objects.filter(file_id=file_id).select_related('downloaded_by')
