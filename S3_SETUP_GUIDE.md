# AWS S3 Setup Guide for T3 Chat

This guide provides step-by-step instructions to set up AWS S3 for storing PDF documents in your T3 Chat application.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Create an AWS Account](#2-create-an-aws-account)
3. [Create an S3 Bucket](#3-create-an-s3-bucket)
4. [Create IAM User and Access Keys](#4-create-iam-user-and-access-keys)
5. [Configure IAM Permissions](#5-configure-iam-permissions)
6. [Configure Environment Variables](#6-configure-environment-variables)
7. [Install Dependencies](#7-install-dependencies)
8. [Test the Setup](#8-test-the-setup)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Prerequisites

Before starting, ensure you have:

- A valid email address for AWS account
- A credit/debit card (AWS Free Tier is available, but card is required for verification)
- Python 3.11+ installed
- Your T3 Chat backend project set up

---

## 2. Create an AWS Account

**Skip this section if you already have an AWS account.**

1. Go to [https://aws.amazon.com/](https://aws.amazon.com/)

2. Click **"Create an AWS Account"** (top right corner)

3. Fill in the required information:
   - Email address
   - AWS account name (e.g., "t3-chat-dev")
   - Password

4. Choose account type: **Personal** (for development)

5. Enter your contact information

6. Enter payment information (you won't be charged if you stay within Free Tier limits)

7. Verify your identity via phone

8. Select the **Basic Support - Free** plan

9. Sign in to the AWS Management Console

---

## 3. Create an S3 Bucket

### Step 3.1: Navigate to S3

1. Sign in to the [AWS Management Console](https://console.aws.amazon.com/)

2. In the search bar at the top, type **"S3"** and click on **"S3"** under Services

### Step 3.2: Create a New Bucket

1. Click the **"Create bucket"** button (orange button)

2. Configure the bucket:

   **General configuration:**
   - **Bucket name:** `t3-chat-documents-YOUR_UNIQUE_ID`
     - Replace `YOUR_UNIQUE_ID` with something unique (e.g., your username or random numbers)
     - Bucket names must be globally unique across all AWS accounts
     - Example: `t3-chat-documents-john2024` or `t3-chat-documents-abc123`
   
   - **AWS Region:** Choose the region closest to your users
     - For India: `ap-south-1` (Mumbai)
     - For US East: `us-east-1` (N. Virginia)
     - For US West: `us-west-2` (Oregon)
     - For Europe: `eu-west-1` (Ireland)
   
   **Note down the region you selected - you'll need it later!**

3. **Object Ownership:**
   - Keep the default: **ACLs disabled (recommended)**

4. **Block Public Access settings for this bucket:**
   - **KEEP ALL CHECKBOXES CHECKED** (Block all public access)
   - This is important for security - your files should not be publicly accessible

5. **Bucket Versioning:**
   - Keep **Disabled** (unless you want version history)

6. **Default encryption:**
   - Keep the default: **Server-side encryption with Amazon S3 managed keys (SSE-S3)**

7. Click **"Create bucket"** at the bottom

### Step 3.3: Verify Bucket Creation

1. You should see your new bucket in the S3 bucket list
2. Click on your bucket name to open it
3. Note the **AWS Region** shown (e.g., `us-east-1`)

---

## 4. Use Existing IAM User and Create Access Keys

### Step 4.1: Navigate to IAM

1. In the AWS Console search bar, type **"IAM"** and click on **"IAM"** under Services

2. In the left sidebar, click **"Users"**

### Step 4.2: Locate Your Existing User

**Since you already have a `t3_chat` user for EC2, we'll reuse it for S3 access.**

1. In the Users list, find and click on your existing user: **`t3_chat`**

2. You should see the user details page

> [!NOTE]
> We're reusing your existing `t3_chat` user to simplify credential management. The custom S3 policy we'll create later will grant this user the necessary S3 permissions while maintaining security.

### Step 4.3: Create Access Keys

1. You should already be on the `t3_chat` user details page

2. Go to the **"Security credentials"** tab

3. Scroll down to **"Access keys"** section

4. Click **"Create access key"**

5. **Use case:**
   - Select **"Application running outside AWS"**
   - Click **"Next"**

6. **Description tag (optional):**
   - Add: `T3 Chat Backend S3 Access`
   - Click **"Create access key"**

7. **IMPORTANT - Save your credentials NOW:**
   
   You will see:
   - **Access key ID:** Something like `AKIAIOSFODNN7EXAMPLE`
   - **Secret access key:** Something like `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`

   **Copy both values and save them securely!**
   
   You can also click **"Download .csv file"** to save them.

   **WARNING:** The secret access key will only be shown ONCE. If you lose it, you'll need to create new keys.

8. Click **"Done"**

---

## 5. Configure IAM Permissions

### Step 5.1: Create a Custom Policy

1. In IAM, click **"Policies"** in the left sidebar

2. Click **"Create policy"**

3. Click the **"JSON"** tab

4. Delete the existing content and paste this policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "T3ChatS3Access",
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:ListBucket",
                "s3:GetBucketLocation"
            ],
            "Resource": [
                "arn:aws:s3:::YOUR_BUCKET_NAME",
                "arn:aws:s3:::YOUR_BUCKET_NAME/*"
            ]
        }
    ]
}
```

5. **IMPORTANT:** Replace `YOUR_BUCKET_NAME` with your actual bucket name (the one you created in Step 3)

   For example, if your bucket is `t3-chat-documents-john2024`:
   ```json
   "Resource": [
       "arn:aws:s3:::t3-chat-documents-john2024",
       "arn:aws:s3:::t3-chat-documents-john2024/*"
   ]
   ```

6. Click **"Next"**

7. **Policy details:**
   - **Policy name:** `T3ChatS3Policy`
   - **Description:** `Allows T3 Chat backend to upload, download, and delete files from S3`

8. Click **"Create policy"**

### Step 5.2: Attach Policy to User

1. Go back to **"Users"** in the left sidebar

2. Click on your user (`t3_chat`)

3. Go to the **"Permissions"** tab

4. Click **"Add permissions"** → **"Add permissions"**

5. Select **"Attach policies directly"**

6. In the search box, type `T3ChatS3Policy`

7. Check the box next to your custom policy

8. Click **"Next"** → **"Add permissions"**

---

## 6. Configure Environment Variables

### Step 6.1: Update Your .env File

Open your backend `.env` file located at `backend/.env` and add the following variables:

```env
# AWS S3 Configuration
AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY_ID_HERE
AWS_SECRET_ACCESS_KEY=YOUR_SECRET_ACCESS_KEY_HERE
AWS_REGION=YOUR_REGION_HERE
S3_BUCKET_NAME=YOUR_BUCKET_NAME_HERE
```

### Step 6.2: Fill in Your Values

Replace the placeholder values with your actual credentials:

| Variable | Description | Example |
|----------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | The Access Key ID from Step 4.3 | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | The Secret Access Key from Step 4.3 | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `AWS_REGION` | The region where you created your bucket | `us-east-1` or `ap-south-1` |
| `S3_BUCKET_NAME` | Your bucket name from Step 3.2 | `t3-chat-documents-john2024` |

### Step 6.3: Example .env File

Here's what your complete S3 section should look like (with example values):

```env
# AWS S3 Configuration
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=us-east-1
S3_BUCKET_NAME=t3-chat-documents-john2024
```

### Step 6.4: Security Warning

**NEVER commit your `.env` file to Git!**

Make sure your `.gitignore` file includes:
```
.env
*.env
```

---

## 7. Install Dependencies

### Step 7.1: Install boto3

Open a terminal in your backend directory and run:

```bash
cd backend
pip install boto3
```

Or if you're using a virtual environment:

```bash
cd backend
# Activate your virtual environment first
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Then install
pip install boto3
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

### Step 7.2: Verify Installation

```bash
python -c "import boto3; print('boto3 installed successfully!')"
```

---

## 8. Test the Setup

### Step 8.1: Create a Test Script

Create a file `backend/test_s3.py` with the following content:

```python
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
        status = "✓ SET" if is_set else "✗ MISSING"
        print(f"   {var}: {status}")
        if not is_set:
            all_good = False
    
    if not all_good:
        print("\n❌ Some environment variables are missing!")
        print("   Please check your .env file.")
        return False
    
    print(f"\n   Region: {settings.aws_region}")
    print(f"   Bucket: {settings.s3_bucket_name}")
    
    # Test S3 connection
    print("\n2. Testing S3 connection...")
    
    try:
        from storage.s3_client import get_s3_client
        s3_client = get_s3_client()
        print("   ✓ S3 client created successfully")
    except Exception as e:
        print(f"   ✗ Failed to create S3 client: {e}")
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
        print(f"   ✓ Upload successful!")
        print(f"   S3 Key: {result['s3_key']}")
    except Exception as e:
        print(f"   ✗ Upload failed: {e}")
        return False
    
    # Test download
    print("\n4. Testing file download...")
    
    try:
        downloaded = s3_client.download_file(result['s3_key'])
        if downloaded == test_content:
            print("   ✓ Download successful! Content matches.")
        else:
            print("   ✗ Downloaded content doesn't match!")
            return False
    except Exception as e:
        print(f"   ✗ Download failed: {e}")
        return False
    
    # Test presigned URL
    print("\n5. Testing presigned URL generation...")
    
    try:
        url = s3_client.get_presigned_url(result['s3_key'], expiration=60)
        print(f"   ✓ Presigned URL generated!")
        print(f"   URL (valid for 60 seconds): {url[:80]}...")
    except Exception as e:
        print(f"   ✗ Presigned URL generation failed: {e}")
        return False
    
    # Test delete
    print("\n6. Testing file deletion...")
    
    try:
        s3_client.delete_file(result['s3_key'])
        print("   ✓ File deleted successfully!")
    except Exception as e:
        print(f"   ✗ Delete failed: {e}")
        return False
    
    # Verify deletion
    print("\n7. Verifying file was deleted...")
    
    try:
        exists = s3_client.file_exists(result['s3_key'])
        if not exists:
            print("   ✓ File no longer exists (deletion confirmed)")
        else:
            print("   ✗ File still exists!")
            return False
    except Exception as e:
        print(f"   ✗ Verification failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✓ ALL TESTS PASSED! S3 is configured correctly.")
    print("=" * 50)
    return True


if __name__ == "__main__":
    success = test_s3_configuration()
    sys.exit(0 if success else 1)
```

### Step 8.2: Run the Test

```bash
cd backend
python test_s3.py
```

### Step 8.3: Expected Output

If everything is configured correctly, you should see:

```
==================================================
S3 Configuration Test
==================================================

1. Checking environment variables...
   AWS_ACCESS_KEY_ID: ✓ SET
   AWS_SECRET_ACCESS_KEY: ✓ SET
   AWS_REGION: ✓ SET
   S3_BUCKET_NAME: ✓ SET

   Region: us-east-1
   Bucket: t3-chat-documents-john2024

2. Testing S3 connection...
   ✓ S3 client created successfully

3. Testing file upload...
   ✓ Upload successful!
   S3 Key: test_user/test_conversation/test_document/test_file.txt

4. Testing file download...
   ✓ Download successful! Content matches.

5. Testing presigned URL generation...
   ✓ Presigned URL generated!
   URL (valid for 60 seconds): https://t3-chat-documents-john2024.s3.us-east-1...

6. Testing file deletion...
   ✓ File deleted successfully!

7. Verifying file was deleted...
   ✓ File no longer exists (deletion confirmed)

==================================================
✓ ALL TESTS PASSED! S3 is configured correctly.
==================================================
```

### Step 8.4: Clean Up Test File

After testing, you can delete the test script:

```bash
# Optional - remove test script
del backend\test_s3.py  # Windows
# or
rm backend/test_s3.py   # macOS/Linux
```

---

## 9. Troubleshooting

### Error: "Access Denied"

**Cause:** IAM policy is not correctly configured or not attached to the user.

**Solution:**
1. Go to IAM → Users → your user
2. Check that `T3ChatS3Policy` is attached
3. Verify the bucket name in the policy matches your actual bucket name
4. Make sure there are no typos in the ARN

### Error: "NoSuchBucket"

**Cause:** Bucket name in `.env` doesn't match the actual bucket.

**Solution:**
1. Go to S3 in AWS Console
2. Copy the exact bucket name
3. Update `S3_BUCKET_NAME` in your `.env` file

### Error: "InvalidAccessKeyId"

**Cause:** Access Key ID is incorrect or has been deleted.

**Solution:**
1. Go to IAM → Users → your user → Security credentials
2. Check if the access key is Active
3. If deleted, create new access keys
4. Update your `.env` file with new credentials

### Error: "SignatureDoesNotMatch"

**Cause:** Secret Access Key is incorrect.

**Solution:**
1. You cannot view the secret key again after creation
2. Delete the existing access key
3. Create new access keys
4. Update your `.env` file with the new secret

### Error: "The bucket you are attempting to access must be addressed using the specified endpoint"

**Cause:** Region mismatch between your configuration and the actual bucket location.

**Solution:**
1. Go to S3 → Click your bucket → Properties
2. Find "AWS Region" 
3. Update `AWS_REGION` in your `.env` to match

### Error: "botocore.exceptions.NoCredentialsError"

**Cause:** Environment variables not loaded or `.env` file not found.

**Solution:**
1. Make sure `.env` file is in the `backend/` directory
2. Check that there are no spaces around `=` in the `.env` file
3. Restart your application after changing `.env`

---

## AWS Free Tier Information

AWS S3 Free Tier includes (for 12 months):
- 5 GB of Standard Storage
- 20,000 GET Requests
- 2,000 PUT Requests

For a typical chat application development, you'll likely stay well within these limits.

**Check your usage:** AWS Console → Billing → Free Tier

---

## Security Best Practices

1. **Never commit credentials to Git**
   - Keep `.env` in `.gitignore`
   - Use environment variables in production

2. **Use least-privilege permissions**
   - The custom policy we created only allows necessary actions
   - Don't use `AmazonS3FullAccess`

3. **Rotate access keys periodically**
   - Create new keys every 90 days
   - Delete old keys after updating your application

4. **Enable MFA on your AWS root account**
   - Go to IAM → Security credentials → Assign MFA device

5. **Monitor S3 usage**
   - Enable S3 access logging if needed
   - Set up billing alerts

---

## Quick Reference

| Item | Value |
|------|-------|
| AWS Console | https://console.aws.amazon.com/ |
| S3 Console | https://s3.console.aws.amazon.com/ |
| IAM Console | https://console.aws.amazon.com/iam/ |
| Your Bucket | `S3_BUCKET_NAME` from `.env` |
| Your Region | `AWS_REGION` from `.env` |

---

## Next Steps

After successful setup:

1. Start your backend server: `uvicorn main:app --reload`
2. Test PDF upload through the frontend
3. Verify files appear in your S3 bucket via AWS Console

Your T3 Chat application is now configured to store PDF documents in AWS S3!
