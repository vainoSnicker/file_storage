from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from files.models import User, Organization, File, Download


class OrganizationListViewTestCase(TestCase):
    """Test cases for OrganizationListView"""
    
    def setUp(self):
        """Set up test data"""
        # Create organizations
        self.org1 = Organization.objects.create(name='Acme Corp')
        self.org2 = Organization.objects.create(name='Globex Industries')
        self.org3 = Organization.objects.create(name='No Downloads Corp')
        
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
            organization=self.org1,
            uploaded_by=self.user1,
            file=test_file2,
            name='file2.txt',
            file_size=len(b'File 2 content'),
            content_type='text/plain'
        )
        
        test_file3 = SimpleUploadedFile(
            name='file3.txt',
            content=b'File 3 content',
            content_type='text/plain'
        )
        self.file3 = File.objects.create(
            organization=self.org2,
            uploaded_by=self.user2,
            file=test_file3,
            name='file3.txt',
            file_size=len(b'File 3 content'),
            content_type='text/plain'
        )
        
        # Create downloads
        # org1 has 3 downloads (2 for file1, 1 for file2)
        Download.objects.create(file=self.file1, downloaded_by=self.user1)
        Download.objects.create(file=self.file1, downloaded_by=self.user2)
        Download.objects.create(file=self.file2, downloaded_by=self.user1)
        # org2 has 1 download
        Download.objects.create(file=self.file3, downloaded_by=self.user2)
        # org3 has no downloads
        
        # Set up API client
        self.client = APIClient()
    
    def test_list_organizations_authenticated(self):
        """Test listing organizations with download counts when authenticated"""
        # Authenticate user
        self.client.login(username='testuser1', password='testpass123')
        
        # Get the list URL
        url = reverse('organizations-list')
        
        # Make the request
        response = self.client.get(url)
        
        # Assert response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # All 3 organizations
    
    def test_list_organizations_unauthenticated(self):
        """Test that unauthenticated users cannot list organizations"""
        # Do not authenticate
        
        url = reverse('organizations-list')
        
        # Make the request
        response = self.client.get(url)
        
        # Assert 403 Forbidden (or 401 Unauthorized)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
    
    def test_download_counts_are_correct(self):
        """Test that download counts are calculated correctly"""
        # Authenticate user
        self.client.login(username='testuser1', password='testpass123')
        
        url = reverse('organizations-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Find organizations in the response
        org1_data = next((o for o in response.data if o['id'] == self.org1.id), None)
        org2_data = next((o for o in response.data if o['id'] == self.org2.id), None)
        org3_data = next((o for o in response.data if o['id'] == self.org3.id), None)
        
        self.assertIsNotNone(org1_data)
        self.assertEqual(org1_data['total_downloads'], 3)  # 2 for file1 + 1 for file2
        
        self.assertIsNotNone(org2_data)
        self.assertEqual(org2_data['total_downloads'], 1)  # 1 for file3
        
        self.assertIsNotNone(org3_data)
        self.assertEqual(org3_data['total_downloads'], 0)  # No downloads

