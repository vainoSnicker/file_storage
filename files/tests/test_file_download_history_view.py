from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from files.models import User, Organization, File, Download


class FileDownloadHistoryViewTestCase(TestCase):
    """Test cases for FileDownloadHistoryView"""
    
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
        self.download1 = Download.objects.create(file=self.file1, downloaded_by=self.user1)
        self.download2 = Download.objects.create(file=self.file1, downloaded_by=self.user2)
        self.download3 = Download.objects.create(file=self.file1, downloaded_by=self.user1)
        
        # file2 has no downloads
        
        # Set up API client
        self.client = APIClient()
    
    def test_list_file_downloads_authenticated(self):
        """Test listing file download history when authenticated"""
        # Authenticate user
        self.client.login(username='testuser1', password='testpass123')
        
        # Get the list URL for file1
        url = reverse('file-download-history', kwargs={'file_id': self.file1.id})
        
        # Make the request
        response = self.client.get(url)
        
        # Assert response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # file1 has 3 downloads
    
    def test_list_file_downloads_unauthenticated(self):
        """Test that unauthenticated users cannot list download history"""
        # Do not authenticate
        
        url = reverse('file-download-history', kwargs={'file_id': self.file1.id})
        
        # Make the request
        response = self.client.get(url)
        
        # Assert 403 Forbidden (or 401 Unauthorized)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
    
    def test_list_shows_only_specified_file_downloads(self):
        """Test that only downloads for the specified file are returned"""
        # Authenticate user
        self.client.login(username='testuser1', password='testpass123')
        
        # Get downloads for file1
        url = reverse('file-download-history', kwargs={'file_id': self.file1.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # file1 has 3 downloads
        
        # Verify the downloads belong to file1
        download_ids = [d['id'] for d in response.data]
        self.assertIn(self.download1.id, download_ids)
        self.assertIn(self.download2.id, download_ids)
        self.assertIn(self.download3.id, download_ids)
        
        # Get downloads for file2 (has no downloads)
        url = reverse('file-download-history', kwargs={'file_id': self.file2.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # file2 has no downloads
    
    def test_list_nonexistent_file_returns_404(self):
        """Test that requesting history for a nonexistent file returns 404"""
        # Authenticate user
        self.client.login(username='testuser1', password='testpass123')
        
        url = reverse('file-download-history', kwargs={'file_id': 99999})
        
        # Make the request
        response = self.client.get(url)
        
        # Assert 404 response
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

