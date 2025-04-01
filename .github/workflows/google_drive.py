import os
import json
import logging
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# The scope we need for uploading files to Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def authenticate_google_drive():
    """
    Authenticate with Google Drive API using service account credentials
    
    Returns:
        google.auth.credentials.Credentials: Credentials for Google API
    """
    try:
        # Get credentials from environment variable
        creds_json = os.environ.get('GOOGLE_DRIVE_CREDENTIALS')
        if not creds_json:
            logger.error("GOOGLE_DRIVE_CREDENTIALS environment variable not found")
            return None
        
        # Load credentials from JSON string
        credentials_info = json.loads(creds_json)
        credentials = Credentials.from_service_account_info(
            credentials_info, scopes=SCOPES
        )
        
        return credentials
    except Exception as e:
        logger.error(f"Error authenticating with Google Drive: {str(e)}")
        return None

def upload_file_to_drive(file_path, folder_id=None, mime_type='application/json'):
    """
    Upload a file to Google Drive
    
    Args:
        file_path (str): Path to the file to upload
        folder_id (str, optional): Google Drive folder ID to upload to. If None, uploads to root.
        mime_type (str, optional): MIME type of the file. Default is 'application/json'.
        
    Returns:
        dict: Response from Google Drive API with file details, or None if upload failed
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            logger.error(f"File not found or empty: {file_path}")
            return None
        
        # Authenticate with Google Drive
        credentials = authenticate_google_drive()
        if not credentials:
            return None
        
        # Build the Drive API client
        drive_service = build('drive', 'v3', credentials=credentials)
        
        # Create a unique filename with timestamp
        original_filename = os.path.basename(file_path)
        filename, extension = os.path.splitext(original_filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"{filename}_{timestamp}{extension}"
        
        # Prepare file metadata
        file_metadata = {
            'name': new_filename
        }
        
        # If folder_id is provided, upload to that folder
        if folder_id:
            file_metadata['parents'] = [folder_id]
        
        # Prepare the file for upload
        media = MediaFileUpload(
            file_path,
            mimetype=mime_type,
            resumable=True
        )
        
        # Upload the file
        uploaded_file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id,name,webViewLink'
        ).execute()
        
        logger.info(f"Successfully uploaded file to Google Drive: {uploaded_file.get('name')}")
        logger.info(f"File ID: {uploaded_file.get('id')}")
        logger.info(f"View file at: {uploaded_file.get('webViewLink')}")
        
        return uploaded_file
    except Exception as e:
        logger.error(f"Error uploading file to Google Drive: {str(e)}")
        return None

def upload_price_history_to_drive(folder_id=None):
    """
    Upload the price_history.json file to Google Drive
    
    Args:
        folder_id (str, optional): Google Drive folder ID to upload to. If None, uploads to root.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        price_history_path = os.path.join('static', 'data', 'price_history.json')
        
        # Check if the file exists and is not empty
        if not os.path.exists(price_history_path) or os.path.getsize(price_history_path) == 0:
            logger.error(f"Price history file not found or empty at {price_history_path}")
            return False
        
        # Read the file to make sure it's valid JSON
        with open(price_history_path, 'r') as f:
            json_data = json.load(f)
            if not json_data:
                logger.error("Price history file contains empty JSON data")
                return False
        
        # Upload the file to Google Drive
        result = upload_file_to_drive(
            file_path=price_history_path,
            folder_id=folder_id,
            mime_type='application/json'
        )
        
        return result is not None
    
    except Exception as e:
        logger.error(f"Error uploading price history to Google Drive: {str(e)}")
        return False