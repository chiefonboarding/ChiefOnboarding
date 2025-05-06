import os
import uuid
from urllib.parse import urljoin

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.urls import reverse


class LocalS3Storage:
    """
    A local storage implementation that mimics the S3 interface.
    This allows for easy switching between local storage and S3 in the future.
    """

    def __init__(self):
        # Create the storage directory if it doesn't exist
        self.storage_dir = getattr(settings, 'MEDIA_ROOT', os.path.join(settings.BASE_DIR, 'media'))
        self.bucket_dir = os.path.join(self.storage_dir, 'local_s3')
        os.makedirs(self.bucket_dir, exist_ok=True)
        
        # Initialize the Django FileSystemStorage
        self.storage = FileSystemStorage(location=self.bucket_dir)
        
        # Base URL for accessing files
        self.base_url = getattr(settings, 'MEDIA_URL', '/media/')
        
    def get_presigned_url(self, key, time=3600):
        """
        Generate a URL for uploading a file.
        For local storage, we'll use a simple URL with a token.
        """
        # Generate a temporary token for this upload
        token = str(uuid.uuid4())
        
        # Store the token in a way that can be validated later
        # In a real implementation, you might want to store this in cache or database
        # For simplicity, we'll just return the URL with the token
        
        # The URL will point to a view that handles the upload
        return reverse('organization:upload_file', kwargs={
            'key': key,
            'token': token
        })
    
    def get_file(self, key, time=604799):
        """
        Generate a URL for accessing a file.
        """
        if not key:
            return ""
            
        # Check if the file exists
        file_path = os.path.join(self.bucket_dir, key)
        if not os.path.exists(file_path):
            return ""
            
        # Return the URL to access the file
        return urljoin(self.base_url, f'local_s3/{key}')
    
    def delete_file(self, key):
        """
        Delete a file from local storage.
        """
        if not key:
            return
            
        # Delete the file if it exists
        file_path = os.path.join(self.bucket_dir, key)
        if os.path.exists(file_path):
            os.remove(file_path)
            
        # Remove empty directories
        self._remove_empty_dirs(os.path.dirname(file_path))
    
    def _remove_empty_dirs(self, directory):
        """
        Recursively remove empty directories.
        """
        if directory == self.bucket_dir:
            return
            
        if os.path.exists(directory) and not os.listdir(directory):
            os.rmdir(directory)
            self._remove_empty_dirs(os.path.dirname(directory))
    
    def save_file(self, key, content):
        """
        Save a file to local storage.
        This method is not part of the S3 interface but is needed for local storage.
        """
        # Ensure the directory exists
        directory = os.path.dirname(os.path.join(self.bucket_dir, key))
        os.makedirs(directory, exist_ok=True)
        
        # Save the file
        return self.storage.save(key, content)
