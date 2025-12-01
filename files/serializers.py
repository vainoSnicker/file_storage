from rest_framework import serializers
from files.models import Organization, User, File, Download


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'name']


class UserSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'organization']


class DownloadSerializer(serializers.ModelSerializer):
    file_name = serializers.CharField(source='file.name', read_only=True)
    downloaded_by_username = serializers.CharField(source='downloaded_by.username', read_only=True)

    class Meta:
        model = Download
        fields = ['id', 'file', 'file_name', 'downloaded_by', 'downloaded_by_username', 'downloaded_at']
        read_only_fields = ['id', 'file', 'downloaded_by', 'downloaded_by_username', 'file_name', 'downloaded_at']


class FileUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ['name', 'file']


class FileDetailSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    uploaded_by_username = serializers.CharField(source='uploaded_by.username', read_only=True)
    download_count = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = [
            'id', 
            'name', 
            'organization', 
            'organization_name', 
            'uploaded_by_username', 
            'uploaded_at',
            'file_size',
            'content_type',
            'download_count',
        ]

    def get_download_count(self, obj):
        if hasattr(obj, 'download_count'):
            return obj.download_count
        return obj.downloads.count() 


class OrganizationWithDownloadCountSerializer(OrganizationSerializer):
    total_downloads = serializers.IntegerField()

    class Meta(OrganizationSerializer.Meta):
        fields = OrganizationSerializer.Meta.fields + ['total_downloads']


class UserDownloadSerializer(serializers.ModelSerializer):
    file_info = FileDetailSerializer(source='file', read_only=True)

    class Meta:
        model = Download
        fields = ['id', 'file_info', 'downloaded_at']


class FileDownloadSerializer(serializers.ModelSerializer):
    user_info = UserSerializer(source='downloaded_by', read_only=True)

    class Meta:
        model = Download
        fields = ['id', 'user_info', 'downloaded_at']
