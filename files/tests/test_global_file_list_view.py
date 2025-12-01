from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from files.models import User, Organization, File, Download


class GlobalFileListViewTestCase(TestCase):
    """Test cases for GlobalFileListView"""
    
    def setUp(self):
        """Set up test data"""
        # Create organizations
        self.org1 = Organization.objects.create(name='Acme Corp')
        self.org2 = Organization.objects.create(name='Globex Industries')
        
        # Create users
        self.user1 = User.objects.create_user(
            username='testuser1',
            password='testpass123',
            organization=self.org1
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            password='testpass123',
            organization=self.org2
        )
        
        # Create files
        test_file1 = SimpleUploadedFile(
            name='file1.txt',
            content=b'File 1 content',
            content_type='text/plain'
        )
        self.file1 = File.objects.create(
            organization=self.org1,
            uploaded_by=self.user1,
            file=test_file1,
            name='file1.txt',
            file_size=len(b'File 1 content'),
            content_type='text/plain'
        )
        
        test_file2 = SimpleUploadedFile(
            name='file2.txt',
            content=b'File 2 content',
            content_type='text/plain'
        )
        self.file2 = File.objects.create(
            organization=self.org2,
            uploaded_by=self.user2,
            file=test_file2,
            name='file2.txt',
            file_size=len(b'File 2 content'),
            content_type='text/plain'
        )
        
        # Create downloads for file1
        Download.objects.create(file=self.file1, downloaded_by=self.user1)
        Download.objects.create(file=self.file1, downloaded_by=self.user2)
        
        # Set up API client
        self.client = APIClient()
    
    def test_list_files_authenticated(self):
        """Test listing all files when authenticated"""
        # Authenticate user
        self.client.login(username='testuser1', password='testpass123')
        
        # Get the list URL
        url = reverse('global-file-list')
        
        # Make the request
        response = self.client.get(url)
        
        # Assert response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        # Check that both files are in the response
        file_names = [file['name'] for file in response.data]
        self.assertIn('file1.txt', file_names)
        self.assertIn('file2.txt', file_names)
    
    def test_list_files_unauthenticated(self):
        """Test that unauthenticated users cannot list files"""
        # Do not authenticate
        
        url = reverse('global-file-list')
        
        # Make the request
        response = self.client.get(url)
        
        # Assert 403 Forbidden (or 401 Unauthorized)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
    
    def test_list_files_includes_download_counts(self):
        """Test that download counts are included in the response"""
        # Authenticate user
        self.client.login(username='testuser1', password='testpass123')
        
        url = reverse('global-file-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Find file1 in the response
        file1_data = next((f for f in response.data if f['id'] == self.file1.id), None)
        self.assertIsNotNone(file1_data)
        self.assertEqual(file1_data['download_count'], 2)  # file1 has 2 downloads
        
        # Find file2 in the response
        file2_data = next((f for f in response.data if f['id'] == self.file2.id), None)
        self.assertIsNotNone(file2_data)
        self.assertEqual(file2_data['download_count'], 0)  # file2 has no downloads
