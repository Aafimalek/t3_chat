# CI/CD Setup Guide for T3 Chat Backend

This guide explains how to set up GitHub Actions CI/CD pipeline to automatically deploy your T3 Chat **backend** to your EC2 instance.

> **Note:** The frontend is hosted on Vercel and deploys automatically when you push to the repository.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Prerequisites](#2-prerequisites)
3. [Step 1: Generate SSH Key for GitHub Actions](#step-1-generate-ssh-key-for-github-actions)
4. [Step 2: Add SSH Key to EC2](#step-2-add-ssh-key-to-ec2)
5. [Step 3: Configure GitHub Secrets](#step-3-configure-github-secrets)
6. [Step 4: Test the Pipeline](#step-4-test-the-pipeline)
7. [How the Pipeline Works](#how-the-pipeline-works)
8. [Troubleshooting](#troubleshooting)
9. [Manual Deployment](#manual-deployment)

---

## 1. Overview

The CI/CD pipeline will:

1. **Trigger** automatically when you push backend changes to the `main` branch
2. **SSH** into your EC2 instance
3. **Pull** the latest code from GitHub
4. **Install** updated dependencies
5. **Restart** the backend service
6. **Verify** the deployment with a health check

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   GitHub    │──────│   GitHub    │──────│    EC2      │
│   (Push)    │      │   Actions   │ SSH  │   Server    │
└─────────────┘      └─────────────┘      └─────────────┘
                            │
                     ┌──────┴──────┐
                     │  1. Pull    │
                     │  2. Install │
                     │  3. Restart │
                     │  4. Verify  │
                     └─────────────┘
```

### Deployment Architecture

| Component | Hosting | Deployment |
|-----------|---------|------------|
| **Frontend** | Vercel | Auto-deploys on push |
| **Backend** | EC2 | GitHub Actions (this guide) |
| **API URL** | `https://api.manimancer.fun` | Points to EC2 |

---

## 2. Prerequisites

Before starting, ensure you have:

- [x] EC2 instance running with backend deployed (see `deployment_guide.md`)
- [x] GitHub repository with your code
- [x] SSH access to your EC2 instance working
- [x] Backend service (`t3-backend`) running via systemd

---

## Step 1: Generate SSH Key for GitHub Actions

You need a dedicated SSH key for GitHub Actions to access your EC2 server.

### Option A: Generate New Key (Recommended)

Run this on your **local machine** (Windows PowerShell, Mac Terminal, or Linux):

```bash
# Generate a new SSH key pair
ssh-keygen -t ed25519 -C "github-actions-deploy" -f github_actions_key -N ""
```

This creates two files:
- `github_actions_key` - Private key (for GitHub Secrets)
- `github_actions_key.pub` - Public key (for EC2)

### Option B: Use Existing Key

If you want to use your existing `t3-backend-key.pem`, you can, but it's less secure.

---

## Step 2: Add SSH Key to EC2

### 2.1: Connect to Your EC2 Instance

```bash
# Windows
ssh -i "t3-backend-key.pem" ubuntu@YOUR_EC2_IP

# Mac/Linux
ssh -i "t3-backend-key.pem" ubuntu@YOUR_EC2_IP
```

### 2.2: Add the Public Key

On your EC2 instance, add the GitHub Actions public key:

```bash
# Open the authorized_keys file
nano ~/.ssh/authorized_keys
```

**Add a new line** at the end with the contents of `github_actions_key.pub`:

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI... github-actions-deploy
```

Save and exit (`Ctrl+O`, `Enter`, `Ctrl+X`).

### 2.3: Verify Key Was Added

```bash
cat ~/.ssh/authorized_keys
```

You should see both your original key and the new GitHub Actions key.

---

## Step 3: Configure GitHub Secrets

### 3.1: Navigate to Repository Settings

1. Go to your GitHub repository
2. Click **Settings** (tab at the top)
3. In the left sidebar, click **Secrets and variables** → **Actions**

### 3.2: Add Required Secrets

Click **"New repository secret"** for each of these:

| Secret Name | Value | Description |
|------------|-------|-------------|
| `EC2_HOST` | `54.123.45.67` | Your EC2 Public IP address |
| `EC2_SSH_KEY` | (see below) | The ENTIRE private key content |

### 3.3: Add EC2_SSH_KEY Secret

**This is the most important step!**

1. Open the private key file (`github_actions_key` or `t3-backend-key.pem`) in a text editor
2. Copy the **ENTIRE** content including:
   ```
   -----BEGIN OPENSSH PRIVATE KEY-----
   b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAA...
   ...
   -----END OPENSSH PRIVATE KEY-----
   ```
3. Paste it as the value for `EC2_SSH_KEY` secret

**Important:** 
- Include the `-----BEGIN` and `-----END` lines
- Don't add extra spaces or newlines
- The entire key must be pasted as-is

### 3.4: Verify Secrets Are Set

Your secrets page should show:
- `EC2_HOST` (updated X seconds ago)
- `EC2_SSH_KEY` (updated X seconds ago)

---

## Step 4: Test the Pipeline

### 4.1: Trigger the Pipeline

**Option A: Push to main branch**
```bash
git add .
git commit -m "Setup CI/CD pipeline"
git push origin main
```

**Option B: Manual trigger**
1. Go to your repository on GitHub
2. Click **Actions** tab
3. Click **Deploy to EC2** workflow
4. Click **Run workflow** → **Run workflow**

### 4.2: Monitor the Deployment

1. Go to **Actions** tab in your repository
2. Click on the running workflow
3. Watch the logs for each step

### 4.3: Expected Output

If successful, you'll see:
```
==========================================
Starting Backend Deployment
==========================================
[1/4] Pulling latest code...
Already up to date.
[2/4] Installing dependencies...
Resolved 25 packages in 1.2s
[3/4] Restarting backend service...
[4/4] Running health check...
✅ Backend deployment successful!
==========================================
Backend Deployment Complete!
==========================================
```

---

## Frontend (Vercel)

The frontend is hosted on **Vercel** and deploys automatically when you push to the repository.

### Vercel Environment Variables

Make sure these are set in your Vercel project settings:

| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | `https://api.manimancer.fun` |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Your Clerk key |
| `CLERK_SECRET_KEY` | Your Clerk secret |

---

## How the Pipeline Works

### Workflow Files

```
.github/
└── workflows/
    ├── deploy.yml    # Backend deployment to EC2
    └── test.yml      # Backend linting
```

### deploy.yml Workflow

```yaml
on:
  push:
    branches: [main]
    paths: ['backend/**']  # Only triggers on backend changes
  workflow_dispatch:        # Allows manual trigger

jobs:
  deploy-backend:
    # 1. Checkout code
    # 2. Setup SSH key from secrets
    # 3. SSH into EC2 and run deployment commands
    # 4. Health check to verify deployment
```

### Deployment Steps on EC2

1. `git fetch && git reset --hard origin/main` - Get latest code
2. `uv sync` - Install Python dependencies
3. `sudo systemctl restart t3-backend` - Restart service
4. `curl http://localhost:8000/health` - Verify it's working

### When Does Deployment Trigger?

| Change | Backend Deploys? | Frontend Deploys? |
|--------|------------------|-------------------|
| `backend/**` files | Yes (GitHub Actions) | No |
| `frontend/**` files | No | Yes (Vercel auto) |
| Other files | No | No |

---

## Troubleshooting

### Error: "Permission denied (publickey)"

**Cause:** SSH key not correctly configured

**Solution:**
1. Verify the public key is in EC2's `~/.ssh/authorized_keys`
2. Check the private key in GitHub Secrets is complete (including BEGIN/END lines)
3. Ensure no extra whitespace in the secret

```bash
# On EC2, check authorized_keys
cat ~/.ssh/authorized_keys

# Test SSH connection manually
ssh -i github_actions_key ubuntu@YOUR_EC2_IP "echo 'SSH works!'"
```

### Error: "Host key verification failed"

**Cause:** EC2 host not in known_hosts

**Solution:** The workflow handles this automatically, but if issues persist:

```bash
# Get the host key
ssh-keyscan -H YOUR_EC2_IP
```

### Error: "Connection refused" during health check

**Cause:** Backend service failed to start

**Solution:**
```bash
# On EC2, check service status
sudo systemctl status t3-backend

# Check logs
sudo journalctl -u t3-backend -n 50 --no-pager

# Common fixes:
# 1. Check .env file has all required variables
# 2. Check MongoDB is running: docker ps
# 3. Check for Python errors in logs
```

### Error: "uv: command not found"

**Cause:** uv not in PATH for SSH session

**Solution:** The workflow sources the env file. If issues persist:

```bash
# On EC2, add to .bashrc
echo 'source $HOME/.local/bin/env' >> ~/.bashrc
```

### Workflow Not Triggering

**Cause:** Various

**Solutions:**
1. Check you're pushing to `main` branch
2. Check the workflow file is in `.github/workflows/`
3. Check for YAML syntax errors
4. Go to Actions tab and check for errors

---

## Manual Deployment

If you need to deploy manually (pipeline is broken):

```bash
# SSH into EC2
ssh -i "t3-backend-key.pem" ubuntu@YOUR_EC2_IP

# Pull and deploy
cd /home/ubuntu/t3_chat
git pull origin main
cd backend
uv sync
sudo systemctl restart t3-backend

# Verify
curl http://localhost:8000/health
```

---

## Security Best Practices

1. **Use dedicated SSH keys** for GitHub Actions (don't reuse your personal key)

2. **Rotate keys periodically** - Generate new keys every 6-12 months

3. **Limit SSH access** - Consider restricting SSH to GitHub's IP ranges in your Security Group

4. **Use branch protection** - Require PR reviews before merging to main

5. **Monitor deployments** - Check Actions logs regularly

---

## Quick Reference

| Item | Location |
|------|----------|
| Workflow files | `.github/workflows/` |
| GitHub Secrets | Repository → Settings → Secrets |
| EC2 SSH keys | `~/.ssh/authorized_keys` on EC2 |
| Backend service | `sudo systemctl status t3-backend` |
| Backend logs | `sudo journalctl -u t3-backend -f` |
| Nginx config | `/etc/nginx/sites-available/t3-backend` |

---

## Next Steps

After setup:

1. Push a small change to `main` branch
2. Watch the deployment in Actions tab
3. Verify changes on your server
4. Set up branch protection rules (optional)
5. Add Slack/Discord notifications (optional)

Your CI/CD pipeline is now ready! Every push to `main` will automatically deploy to your EC2 instance.
