from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from files.models import User, Organization, File, Download


class FileDownloadViewTestCase(TestCase):
    """Test cases for FileDownloadView"""
    
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
        
        # Create a test file
        self.test_file_content = b'Test file content for download'
        self.test_file = SimpleUploadedFile(
            name='test_file.txt',
            content=self.test_file_content,
            content_type='text/plain'
        )
        
        # Create a File instance
        self.file_obj = File.objects.create(
            organization=self.org1,
            uploaded_by=self.user1,
            file=self.test_file,
            name='test_file.txt',
            file_size=len(self.test_file_content),
            content_type='text/plain'
        )
        
        # Set up API client
        self.client = APIClient()
    
    def test_file_download_success(self):
        """Test successful file download"""
        # Authenticate user using session (matches SessionAuthentication)
        self.client.login(username='testuser1', password='testpass123')
        
        # Get the download URL
        url = reverse('file-download', kwargs={'file_id': self.file_obj.id})
        
        # Make the request
        response = self.client.get(url)
        
        # Assert response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Assert file content - FileResponse uses streaming_content
        if hasattr(response, 'streaming_content'):
            content = b''.join(response.streaming_content)
        else:
            content = response.content
        self.assertEqual(content, self.test_file_content)
        
        # Assert headers
        self.assertIn('Content-Disposition', response)
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('test_file.txt', response['Content-Disposition'])
        self.assertEqual(response['Content-Type'], 'text/plain')
        self.assertEqual(response['Content-Length'], str(len(self.test_file_content)))
    
    def test_file_download_creates_download_record(self):
        """Test that downloading a file creates a Download record"""
        # Ensure no downloads exist initially
        initial_count = Download.objects.count()
        
        # Authenticate user using session
        self.client.login(username='testuser1', password='testpass123')
        
        # Get the download URL
        url = reverse('file-download', kwargs={'file_id': self.file_obj.id})
        
        # Make the request
        response = self.client.get(url)
        
        # Assert download was created
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Download.objects.count(), initial_count + 1)
        
        # Assert download record details
        download = Download.objects.get(file=self.file_obj, downloaded_by=self.user1)
        self.assertEqual(download.file, self.file_obj)
        self.assertEqual(download.downloaded_by, self.user1)
    
    def test_file_download_multiple_downloads_create_multiple_records(self):
        """Test that multiple downloads create multiple Download records"""
        # Authenticate user using session
        self.client.login(username='testuser1', password='testpass123')
        
        url = reverse('file-download', kwargs={'file_id': self.file_obj.id})
        
        # Download 3 times
        for _ in range(3):
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Assert 3 download records were created
        self.assertEqual(Download.objects.filter(file=self.file_obj).count(), 3)
    
    def test_file_download_different_users_create_separate_records(self):
        """Test that different users downloading the same file create separate records"""
        # Authenticate first user
        self.client.login(username='testuser1', password='testpass123')
        url = reverse('file-download', kwargs={'file_id': self.file_obj.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Authenticate second user
        self.client.logout()
        self.client.login(username='testuser2', password='testpass123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Assert 2 download records exist
        self.assertEqual(Download.objects.filter(file=self.file_obj).count(), 2)
        
        # Assert both users have download records
        self.assertTrue(Download.objects.filter(file=self.file_obj, downloaded_by=self.user1).exists())
        self.assertTrue(Download.objects.filter(file=self.file_obj, downloaded_by=self.user2).exists())
    
    def test_file_download_404_nonexistent_file(self):
        """Test that downloading a nonexistent file returns 404"""
        # Authenticate user using session
        self.client.login(username='testuser1', password='testpass123')
        
        # Use a non-existent file ID
        url = reverse('file-download', kwargs={'file_id': 99999})
        
        # Make the request
        response = self.client.get(url)
        
        # Assert 404 response
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_file_download_unauthorized(self):
        """Test that unauthenticated users cannot download files"""
        # Do not authenticate
        
        # Get the download URL
        url = reverse('file-download', kwargs={'file_id': self.file_obj.id})
        
        # Make the request
        response = self.client.get(url)
        
        # Assert 403 Forbidden (or 401 Unauthorized depending on DRF settings)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
    
    def test_file_download_content_disposition_header(self):
        """Test that Content-Disposition header is correctly set"""
        # Authenticate user using session
        self.client.login(username='testuser1', password='testpass123')
        
        url = reverse('file-download', kwargs={'file_id': self.file_obj.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content_disposition = response['Content-Disposition']
        self.assertIn('attachment', content_disposition)
        self.assertIn('filename="test_file.txt"', content_disposition)
    
    def test_file_download_content_type_header(self):
        """Test that Content-Type header is correctly set"""
        # Authenticate user using session
        self.client.login(username='testuser1', password='testpass123')
        
        url = reverse('file-download', kwargs={'file_id': self.file_obj.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/plain')
    
    def test_file_download_content_type_fallback(self):
        """Test that Content-Type falls back to application/octet-stream when not set"""
        # Create a file without content_type
        test_file2 = SimpleUploadedFile(
            name='test_file2.bin',
            content=b'Binary content',
            content_type=''
        )
        file_obj2 = File.objects.create(
            organization=self.org1,
            uploaded_by=self.user1,
            file=test_file2,
            name='test_file2.bin',
            file_size=len(b'Binary content'),
            content_type=None
        )
        
        # Authenticate user using session
        self.client.login(username='testuser1', password='testpass123')
        
        url = reverse('file-download', kwargs={'file_id': file_obj2.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should fall back to application/octet-stream
        self.assertEqual(response['Content-Type'], 'application/octet-stream')

