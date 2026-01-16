"""
Storage module for file storage operations.
Provides S3 client for storing PDFs and other binary files.
"""

from storage.s3_client import S3Client, get_s3_client

__all__ = [
    "S3Client",
    "get_s3_client",
]
