import os
import shutil
from datetime import datetime, timedelta
from django.conf import settings

def cleanup_temp_files():
    """
    Cleanup temporary image files that are older than 24 hours.
    This should be run as a scheduled task (e.g., via cron job)
    """
    try:
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_images')
        
        # Skip if directory doesn't exist
        if not os.path.exists(temp_dir):
            return
        
        # Get current time
        now = datetime.now()
        
        # Iterate through all subdirectories in the temp_images directory
        for subdir in os.listdir(temp_dir):
            subdir_path = os.path.join(temp_dir, subdir)
            
            # Skip if not a directory
            if not os.path.isdir(subdir_path):
                continue
            
            # Check directory creation time
            dir_creation_time = datetime.fromtimestamp(os.path.getctime(subdir_path))
            
            # If older than 24 hours (1 day), remove it
            if now - dir_creation_time > timedelta(days=1):
                shutil.rmtree(subdir_path)
                print(f"Removed temp directory: {subdir_path}")
                
    except Exception as e:
        print(f"Error cleaning up temporary files: {str(e)}")