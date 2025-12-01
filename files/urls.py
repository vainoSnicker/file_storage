# file_storage_app/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views
from files import views


urlpatterns = [
    path(
        'auth/login/', 
        auth_views.LoginView.as_view(), 
        name='login'
    ),
    path(
        'organizations/', 
        views.OrganizationListView.as_view(), 
        name='organizations-list'
    ),
    path(
        'organizations/<int:org_id>/files/',
        views.FileListCreateView.as_view(), 
        name='organization-file-list-create'
    ),
    path(
        'files/', 
        views.GlobalFileListView.as_view(), 
        name='global-file-list'
    ),
    path(
        'files/<int:file_id>/download/', 
        views.FileDownloadView.as_view(), 
        name='file-download'
    ),
    path(
        'users/<int:user_id>/downloads/', 
        views.UserDownloadHistoryView.as_view(), 
        name='user-download-history'
    ),
    path(
        'files/<int:file_id>/downloads/', 
        views.FileDownloadHistoryView.as_view(), 
        name='file-download-history'
    ),
]
