from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from files.models import User, Organization, File, Download


class FileListCreateViewTestCase(TestCase):
    """Test cases for FileListCreateView"""
    
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
        
        # Create existing files for testing list functionality
        test_file_content = b'Existing file content'
        test_file = SimpleUploadedFile(
            name='existing_file.txt',
            content=test_file_content,
            content_type='text/plain'
        )
        self.existing_file = File.objects.create(
            organization=self.org1,
            uploaded_by=self.user1,
            file=test_file,
            name='existing_file.txt',
            file_size=len(test_file_content),
            content_type='text/plain'
        )
        
        # Set up API client
        self.client = APIClient()
    
    def test_list_files_authenticated(self):
        """Test listing files for an organization when authenticated"""
        # Authenticate user
        self.client.login(username='testuser1', password='testpass123')
        
        # Get the list URL
        url = reverse('organization-file-list-create', kwargs={'org_id': self.org1.id})
        
        # Make the request
        response = self.client.get(url)
        
        # Assert response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        # FileUploadSerializer only has 'name' and 'file' fields
        self.assertEqual(response.data[0]['name'], 'existing_file.txt')
        self.assertIn('file', response.data[0])  # file field contains the file URL
    
    def test_list_files_unauthenticated(self):
        """Test that unauthenticated users cannot list files"""
        # Do not authenticate
        
        url = reverse('organization-file-list-create', kwargs={'org_id': self.org1.id})
        
        # Make the request
        response = self.client.get(url)
        
        # Assert 403 Forbidden (or 401 Unauthorized)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
    
    def test_list_files_only_shows_organization_files(self):
        """Test that listing files only shows files from the specified organization"""
        # Create a file in org2
        test_file_content2 = b'Org2 file content'
        test_file2 = SimpleUploadedFile(
            name='org2_file.txt',
            content=test_file_content2,
            content_type='text/plain'
        )
        org2_file = File.objects.create(
            organization=self.org2,
            uploaded_by=self.user2,
            file=test_file2,
            name='org2_file.txt',
            file_size=len(test_file_content2),
            content_type='text/plain'
        )
        
        # Authenticate user1 (belongs to org1)
        self.client.login(username='testuser1', password='testpass123')
        
        # List files for org1
        url = reverse('organization-file-list-create', kwargs={'org_id': self.org1.id})
        response = self.client.get(url)
        
        # Should only see org1 files
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'existing_file.txt')
        
        # List files for org2
        url = reverse('organization-file-list-create', kwargs={'org_id': self.org2.id})
        response = self.client.get(url)
        
        # Should only see org2 files
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'org2_file.txt')
    
    def test_upload_file_to_own_organization(self):
        """Test that users can upload files to their own organization"""
        # Authenticate user1 (belongs to org1)
        self.client.login(username='testuser1', password='testpass123')
        
        # Prepare file upload
        test_file_content = b'New file content'
        test_file = SimpleUploadedFile(
            name='new_file.txt',
            content=test_file_content,
            content_type='text/plain'
        )
        
        url = reverse('organization-file-list-create', kwargs={'org_id': self.org1.id})
        
        # Make the upload request
        data = {
            'name': 'new_file.txt',
            'file': test_file
        }
        response = self.client.post(url, data, format='multipart')
        
        # Assert response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Assert file was created
        self.assertTrue(File.objects.filter(name='new_file.txt', organization=self.org1).exists())
        uploaded_file = File.objects.get(name='new_file.txt', organization=self.org1)
        self.assertEqual(uploaded_file.uploaded_by, self.user1)
        self.assertEqual(uploaded_file.organization, self.org1)
        self.assertEqual(uploaded_file.file_size, len(test_file_content))
        self.assertEqual(uploaded_file.content_type, 'text/plain')
    
    def test_upload_file_to_different_organization_forbidden(self):
        """Test that users cannot upload files to a different organization"""
        # Authenticate user1 (belongs to org1)
        self.client.login(username='testuser1', password='testpass123')
        
        # Try to upload to org2 (user1's organization is org1)
        test_file_content = b'Unauthorized file content'
        test_file = SimpleUploadedFile(
            name='unauthorized_file.txt',
            content=test_file_content,
            content_type='text/plain'
        )
        
        url = reverse('organization-file-list-create', kwargs={'org_id': self.org2.id})
        
        data = {
            'name': 'unauthorized_file.txt',
            'file': test_file
        }
        response = self.client.post(url, data, format='multipart')
        
        # Assert 403 Forbidden
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Assert file was NOT created
        self.assertFalse(File.objects.filter(name='unauthorized_file.txt').exists())
    
    def test_upload_file_unauthenticated(self):
        """Test that unauthenticated users cannot upload files"""
        # Do not authenticate
        
        test_file_content = b'Unauthenticated file content'
        test_file = SimpleUploadedFile(
            name='unauthenticated_file.txt',
            content=test_file_content,
            content_type='text/plain'
        )
        
        url = reverse('organization-file-list-create', kwargs={'org_id': self.org1.id})
        
        data = {
            'name': 'unauthenticated_file.txt',
            'file': test_file
        }
        response = self.client.post(url, data, format='multipart')
        
        # Assert 403 Forbidden (or 401 Unauthorized)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
        
        # Assert file was NOT created
        self.assertFalse(File.objects.filter(name='unauthenticated_file.txt').exists())
    
    def test_upload_file_creates_with_correct_attributes(self):
        """Test that uploaded files have correct attributes set"""
        # Authenticate user
        self.client.login(username='testuser1', password='testpass123')
        
        test_file_content = b'Test content for attributes'
        test_file = SimpleUploadedFile(
            name='attributes_test.txt',
            content=test_file_content,
            content_type='text/csv'
        )
        
        url = reverse('organization-file-list-create', kwargs={'org_id': self.org1.id})
        
        data = {
            'name': 'attributes_test.txt',
            'file': test_file
        }
        response = self.client.post(url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify all attributes
        uploaded_file = File.objects.get(name='attributes_test.txt')
        self.assertEqual(uploaded_file.uploaded_by, self.user1)
        self.assertEqual(uploaded_file.organization, self.org1)
        self.assertEqual(uploaded_file.file_size, len(test_file_content))
        self.assertEqual(uploaded_file.content_type, 'text/csv')
    
    def test_upload_multiple_files_to_same_organization(self):
        """Test that multiple files can be uploaded to the same organization"""
        # Authenticate user
        self.client.login(username='testuser1', password='testpass123')
        
        url = reverse('organization-file-list-create', kwargs={'org_id': self.org1.id})
        
        initial_count = File.objects.filter(organization=self.org1).count()
        
        # Upload first file
        test_file1 = SimpleUploadedFile(
            name='file1.txt',
            content=b'Content 1',
            content_type='text/plain'
        )
        data1 = {'name': 'file1.txt', 'file': test_file1}
        response1 = self.client.post(url, data1, format='multipart')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        # Upload second file
        test_file2 = SimpleUploadedFile(
            name='file2.txt',
            content=b'Content 2',
            content_type='text/plain'
        )
        data2 = {'name': 'file2.txt', 'file': test_file2}
        response2 = self.client.post(url, data2, format='multipart')
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        
        # Verify both files were created
        final_count = File.objects.filter(organization=self.org1).count()
        self.assertEqual(final_count, initial_count + 2)

