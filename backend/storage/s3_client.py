"""
S3 Client for file storage operations.
Handles upload, download, delete, and presigned URL generation for S3.
"""

import uuid
from datetime import datetime
from typing import Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from config import get_settings


class S3Client:
    """
    AWS S3 client for file storage operations.
    
    Supports both AWS S3 and S3-compatible services (MinIO, DigitalOcean Spaces, etc.)
    """
    
    def __init__(self):
        settings = get_settings()
        
        if not settings.s3_configured:
            raise ValueError(
                "S3 is not configured. Please set AWS_ACCESS_KEY_ID, "
                "AWS_SECRET_ACCESS_KEY, and S3_BUCKET_NAME environment variables."
            )
        
        self.bucket_name = settings.s3_bucket_name
        self.region = settings.aws_region
        
        # Configure S3 client
        client_kwargs = {
            "service_name": "s3",
            "aws_access_key_id": settings.aws_access_key_id,
            "aws_secret_access_key": settings.aws_secret_access_key,
            "region_name": settings.aws_region,
        }
        
        # Support for S3-compatible services (MinIO, DigitalOcean Spaces, etc.)
        if settings.s3_endpoint_url:
            client_kwargs["endpoint_url"] = settings.s3_endpoint_url
        
        self.client = boto3.client(**client_kwargs)
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self) -> None:
        """Ensure the S3 bucket exists, create if it doesn't."""
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "404":
                # Bucket doesn't exist, create it
                try:
                    if self.region == "us-east-1":
                        # us-east-1 doesn't support LocationConstraint
                        self.client.create_bucket(Bucket=self.bucket_name)
                    else:
                        self.client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={
                                "LocationConstraint": self.region
                            }
                        )
                    print(f"[S3] Created bucket: {self.bucket_name}")
                except ClientError as create_error:
                    print(f"[S3] Failed to create bucket: {create_error}")
                    raise
            else:
                print(f"[S3] Error checking bucket: {e}")
                raise
    
    def generate_key(
        self,
        filename: str,
        user_id: str,
        conversation_id: str,
        document_id: str,
    ) -> str:
        """
        Generate a unique S3 key for a file.
        
        Format: {user_id}/{conversation_id}/{document_id}/{filename}
        """
        # Sanitize filename to remove problematic characters
        safe_filename = "".join(
            c if c.isalnum() or c in ".-_" else "_" for c in filename
        )
        return f"{user_id}/{conversation_id}/{document_id}/{safe_filename}"
    
    def upload_file(
        self,
        file_content: bytes,
        filename: str,
        user_id: str,
        conversation_id: str,
        document_id: str,
        content_type: str = "application/pdf",
        metadata: Optional[dict] = None,
    ) -> dict:
        """
        Upload a file to S3.
        
        Args:
            file_content: File bytes to upload
            filename: Original filename
            user_id: User identifier
            conversation_id: Conversation identifier
            document_id: Document identifier
            content_type: MIME type of the file
            metadata: Optional metadata to store with the file
            
        Returns:
            dict with s3_key, s3_url, and bucket_name
        """
        s3_key = self.generate_key(filename, user_id, conversation_id, document_id)
        
        # Prepare metadata
        file_metadata = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "document_id": document_id,
            "original_filename": filename,
            "uploaded_at": datetime.utcnow().isoformat(),
        }
        if metadata:
            file_metadata.update(metadata)
        
        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type,
                Metadata=file_metadata,
            )
            
            # Generate the S3 URL
            settings = get_settings()
            if settings.s3_endpoint_url:
                s3_url = f"{settings.s3_endpoint_url}/{self.bucket_name}/{s3_key}"
            else:
                s3_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
            
            print(f"[S3] Uploaded file: {s3_key}")
            
            return {
                "s3_key": s3_key,
                "s3_url": s3_url,
                "bucket_name": self.bucket_name,
            }
            
        except ClientError as e:
            print(f"[S3] Upload failed: {e}")
            raise RuntimeError(f"Failed to upload file to S3: {e}")
        except NoCredentialsError:
            raise RuntimeError("AWS credentials not configured properly")
    
    def download_file(self, s3_key: str) -> bytes:
        """
        Download a file from S3.
        
        Args:
            s3_key: The S3 key of the file to download
            
        Returns:
            File content as bytes
        """
        try:
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key,
            )
            return response["Body"].read()
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "NoSuchKey":
                raise FileNotFoundError(f"File not found in S3: {s3_key}")
            print(f"[S3] Download failed: {e}")
            raise RuntimeError(f"Failed to download file from S3: {e}")
    
    def delete_file(self, s3_key: str) -> bool:
        """
        Delete a file from S3.
        
        Args:
            s3_key: The S3 key of the file to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key,
            )
            print(f"[S3] Deleted file: {s3_key}")
            return True
        except ClientError as e:
            print(f"[S3] Delete failed: {e}")
            raise RuntimeError(f"Failed to delete file from S3: {e}")
    
    def get_presigned_url(
        self,
        s3_key: str,
        expiration: int = 3600,
        http_method: str = "GET",
    ) -> str:
        """
        Generate a presigned URL for temporary access to a file.
        
        Args:
            s3_key: The S3 key of the file
            expiration: URL expiration time in seconds (default: 1 hour)
            http_method: HTTP method for the presigned URL (GET or PUT)
            
        Returns:
            Presigned URL string
        """
        try:
            client_method = "get_object" if http_method == "GET" else "put_object"
            url = self.client.generate_presigned_url(
                ClientMethod=client_method,
                Params={
                    "Bucket": self.bucket_name,
                    "Key": s3_key,
                },
                ExpiresIn=expiration,
            )
            return url
        except ClientError as e:
            print(f"[S3] Presigned URL generation failed: {e}")
            raise RuntimeError(f"Failed to generate presigned URL: {e}")
    
    def file_exists(self, s3_key: str) -> bool:
        """
        Check if a file exists in S3.
        
        Args:
            s3_key: The S3 key to check
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            self.client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key,
            )
            return True
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "404":
                return False
            raise


# Singleton instance
_s3_client: Optional[S3Client] = None


def get_s3_client() -> S3Client:
    """Get the S3 client singleton."""
    global _s3_client
    if _s3_client is None:
        _s3_client = S3Client()
    return _s3_client
