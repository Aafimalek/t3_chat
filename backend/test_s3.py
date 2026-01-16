"""
Test script to verify S3 configuration.
Run this from the backend directory: python test_s3.py
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from config import get_settings

def test_s3_configuration():
    """Test that S3 is properly configured."""
    print("=" * 50)
    print("S3 Configuration Test")
    print("=" * 50)
    
    settings = get_settings()
    
    # Check if S3 is configured
    print("\n1. Checking environment variables...")
    
    checks = {
        "AWS_ACCESS_KEY_ID": bool(settings.aws_access_key_id),
        "AWS_SECRET_ACCESS_KEY": bool(settings.aws_secret_access_key),
        "AWS_REGION": bool(settings.aws_region),
        "S3_BUCKET_NAME": bool(settings.s3_bucket_name),
    }
    
    all_good = True
    for var, is_set in checks.items():
        status = "SET" if is_set else "MISSING"
        print(f"   {var}: {status}")
        if not is_set:
            all_good = False
    
    if not all_good:
        print("\nSome environment variables are missing!")
        print("   Please check your .env file.")
        return False
    
    print(f"\n   Region: {settings.aws_region}")
    print(f"   Bucket: {settings.s3_bucket_name}")
    
    # Test S3 connection
    print("\n2. Testing S3 connection...")
    
    try:
        from storage.s3_client import get_s3_client
        s3_client = get_s3_client()
        print("   S3 client created successfully")
    except Exception as e:
        print(f"   Failed to create S3 client: {e}")
        return False
    
    # Test upload
    print("\n3. Testing file upload...")
    
    try:
        test_content = b"Hello, this is a test file for T3 Chat S3 setup!"
        result = s3_client.upload_file(
            file_content=test_content,
            filename="test_file.txt",
            user_id="test_user",
            conversation_id="test_conversation",
            document_id="test_document",
            content_type="text/plain",
        )
        print(f"   Upload successful!")
        print(f"   S3 Key: {result['s3_key']}")
    except Exception as e:
        print(f"   Upload failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test download
    print("\n4. Testing file download...")
    
    try:
        downloaded = s3_client.download_file(result['s3_key'])
        if downloaded == test_content:
            print("   Download successful! Content matches.")
        else:
            print("   Downloaded content doesn't match!")
            return False
    except Exception as e:
        print(f"   Download failed: {e}")
        return False
    
    # Test presigned URL
    print("\n5. Testing presigned URL generation...")
    
    try:
        url = s3_client.get_presigned_url(result['s3_key'], expiration=60)
        print(f"   Presigned URL generated!")
        print(f"   URL (valid for 60 seconds): {url[:80]}...")
    except Exception as e:
        print(f"   Presigned URL generation failed: {e}")
        return False
    
    # Test delete
    print("\n6. Testing file deletion...")
    
    try:
        s3_client.delete_file(result['s3_key'])
        print("   File deleted successfully!")
    except Exception as e:
        print(f"   Delete failed: {e}")
        return False
    
    # Verify deletion
    print("\n7. Verifying file was deleted...")
    
    try:
        exists = s3_client.file_exists(result['s3_key'])
        if not exists:
            print("   File no longer exists (deletion confirmed)")
        else:
            print("   File still exists!")
            return False
    except Exception as e:
        print(f"   Verification failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("ALL TESTS PASSED! S3 is configured correctly.")
    print("=" * 50)
    return True


if __name__ == "__main__":
    try:
        success = test_s3_configuration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
