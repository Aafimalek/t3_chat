# Deploying T3.chat Backend to AWS EC2 (Detailed Guide)

This guide is designed for absolute precision. Follow every step exactly.

## ⚠️ Important: Root vs. IAM User

**Question:** Should I use the Root user or an IAM user?
**Answer:** **ALWAYS use an IAM User.**

-   **Root User**: The account owner. It has unlimited access. If hacked, you lose everything. Use this ONLY to create your first IAM user.
-   **IAM User**: An admin user you create for daily tasks.

### Phase 0: Create an IAM Admin User (If you haven't already)

1.  **Log in** to the AWS Console using your **Root User** email and password.
2.  In the search bar at the top, type `IAM` and select **IAM**.
3.  In the left sidebar, click **Users**.
4.  Click the orange **Create user** button.
5.  **User details**:
    -   **User name**: `AdminUser` (or your preferred name).
    -   Click **Next**.
6.  **Permissions**:
    -   Select **Attach policies directly**.
    -   In the "Permission policies" search box, type `AdministratorAccess`.
    -   Check the box next to **AdministratorAccess**. (This gives full access but is safer to use than Root).
    -   Click **Next**.
7.  **Review**:
    -   Click **Create user**.
8.  **Get Credentials**:
    -   Click on the newly created user name (`AdminUser`) in the list.
    -   Go to the **Security credentials** tab.
    -   Scroll to **Console sign-in**. Click **Enable console access**.
    -   Select **Enable**.
    -   Choose **Custom password** and set a password.
    -   Click **Apply**.
    -   **Log out** of the Root account.
    -   **Log in** using the **IAM User** credentials (you will need your numerical **Account ID**, which you can find in the top right menu of the console).

---

### Phase 1: generating Keys

You need two types of keys: **AWS Key Pair** (to access the server) and **Groq API Key** (for the AI).

#### 1. Generate Groq API Key
1.  Go to [console.groq.com](https://console.groq.com/keys).
2.  Log in.
3.  Click **Create API Key**.
4.  Name it `t3-chat-backend`.
5.  **COPY the key immediately**. It starts with `gsk_`. You will never see it again.
6.  Save it temporarily in a Notepad file on your computer.

#### 2. Generate AWS EC2 Key Pair (SSH Key)
*Do this during the instance creation process specifically for the region you are using.*

---

### Phase 2: Launch EC2 Instance

1.  Log in to AWS Console with your **IAM User**.
2.  Check your **Region** in the top right (e.g., **N. Virginia us-east-1**). Remember this.
3.  Search for **EC2** and click it.
4.  Click the orange **Launch Instance** button.
5.  **Name and tags**:
    -   Name: `t3-chat-backend`
6.  **Application and OS Images (AMI)**:
    -   Select **Ubuntu**.
    -   AMI: Ensure it says **Ubuntu Server 24.04 LTS (HVM)**, SSD Volume Type.
7.  **Instance Type**:
    -   Select `t2.micro` (Free Tier eligible) or `t3.small` (Better performance).
8.  **Key pair (login)**:
    -   Click **Create new key pair**.
    -   **Key pair name**: `t3-backend-key`
    -   **Key pair type**: `RSA`
    -   **Private key file format**: `.pem` (For OpenSSH/Mac/Linux/Windows PowerShell).
    -   Click **Create key pair**.
    -   **ACTION**: A file named `t3-backend-key.pem` will automatically download.
    -   **CRITICAL**: Move this file to a safe folder (e.g., `C:\Users\YourName\.ssh\` or just your Desktop). **Do not lose it.**
9.  **Network settings**:
    -   Click **Edit** (top right of this box).
    -   **Auto-assign public IP**: **Enable**.
    -   **Firewall (security groups)**: select **Create security group**.
    -   **Security group name**: `t3-chat-sg`
    -   **Description**: `Allow SSH, HTTP, HTTPS`
    -   **Inbound Security Group Rules** (Add these carefully):
        -   **Rule 1 (SSH)**: Type: `SSH` | Protocol: `TCP` | Port: `22` | Source: `My IP` (Best for security).
        -   **Rule 2 (HTTP)**: Click **Add security group rule**. Type: `HTTP` | Protocol: `TCP` | Port: `80` | Source: `Anywhere (0.0.0.0/0)`.
        -   **Rule 3 (HTTPS)**: Click **Add security group rule**. Type: `HTTPS` | Protocol: `TCP` | Port: `443` | Source: `Anywhere (0.0.0.0/0)`.
10. **Configure storage**:
    -   Default (8 GiB) is fine, or increase to 20 GiB.
11. Click **Launch Instance** (Orange button on the right).
12. Click the **Instance ID** (e.g., `i-0abcdef12345`) to view your running instance.
13. Wait until **Instance state** is `Running` and **Status check** is `2/2 checks passed`.
14. Copy the **Public IPv4 address** (e.g., `54.123.45.67`).

---

### Phase 3. Connect to the Server

### Option A: Mac/Linux
1.  Open Terminal where the key is.
2.  `chmod 400 t3-backend-key.pem`
3.  `ssh -i "t3-backend-key.pem" ubuntu@YOUR_PUBLIC_IP`

### Option B: Windows (Crucial Step!)
Windows permissions are too open by default. You MUST run these commands in PowerShell to fix the key permissions, or SSH will reject it.

1.  **Open PowerShell** and `cd` to where your key is.
2.  **Reset permissions**:
    ```powershell
    icacls.exe "t3-backend-key.pem" /reset
    ```
3.  **Grant Read-Only access to you**:
    ```powershell
    icacls.exe "t3-backend-key.pem" /grant:r "$($env:USERNAME):(R)"
    ```
4.  **Remove inherited permissions**:
    ```powershell
    icacls.exe "t3-backend-key.pem" /inheritance:r
    ```
5.  **Connect**:
    ```powershell
    ssh -i "t3-backend-key.pem" ubuntu@YOUR_PUBLIC_IP
    ```

---

### Phase 4: Server Setup

Run these commands one by one in the IAM server terminal.

1.  **Update System**:
    ```bash
    sudo apt update && sudo apt upgrade -y
    ```

2.  **Install Essentials (Nginx, Git, Docker)**:
    ```bash
    sudo apt install nginx git docker.io -y
    ```

3.  **Enable Docker**:
    ```bash
    sudo usermod -aG docker $USER
    newgrp docker
    ```

4.  **Install `uv` (Faster Python Tool)**:
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.local/bin/env
    ```

---

### Phase 5: Deploy Code

1.  **Clone Repository**:
    ```bash
    git clone https://github.com/Aafimalek/t3_chat.git
    cd t3_chat/backend
    ```

2.  **Create .env Configuration**:
    ```bash
    nano .env
    ```

3.  **Paste Secrets**:
    Copy the text below, replace the key, and **Right-Click** in the Powershell/Terminal window to paste.
    ```env
    GROQ_API_KEY=gsk_your_key_from_phase_1
    MONGODB_URL=mongodb://localhost:27017
    DATABASE_NAME=t3_chat
    ```
4.  **Save & Exit**:
    -   Press `Ctrl` + `O` then `Enter` (Write Out).
    -   Press `Ctrl` + `X` (Exit).

5.  **Install Python & Dependencies**:
    ```bash
    uv python install 3.13
    uv sync
    ```

---

### Phase 6: Setup Database & Backend Service

1.  **Start MongoDB (using Docker)**:
    ```bash
    docker run -d --restart unless-stopped --name mongodb -p 27017:27017 -v mongo_data:/data/db mongo:latest
    ```

2.  **Create Backend System Service** (Keeps app running):
    ```bash
    sudo nano /etc/systemd/system/t3-backend.service
    ```
    Paste this exactly:
    ```ini
    [Unit]
    Description=T3 Chat Backend
    After=network.target

    [Service]
    User=ubuntu
    Group=ubuntu
    WorkingDirectory=/home/ubuntu/t3_chat/backend
    Environment="PATH=/home/ubuntu/.local/bin:/usr/local/bin:/usr/bin:/bin"
    ExecStart=/home/ubuntu/.local/bin/uv run uvicorn main:app --host 0.0.0.0 --port 8000
    Restart=always

    [Install]
    WantedBy=multi-user.target
    ```
    Save (`Ctrl+O`, `Enter`, `Ctrl+X`).

3.  **Enable Backend**:
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl start t3-backend
    sudo systemctl enable t3-backend
    ```

---

### Phase 7: Public Access (Nginx Reverse Proxy)

1.  **Edit Nginx Config**:
    ```bash
    sudo nano /etc/nginx/sites-available/t3-backend
    ```
    Paste this:
    ```nginx
    server {
        listen 80;
        server_name _;

        location / {
            proxy_pass http://127.0.0.1:8000;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
        }
    }
    ```
    Save (`Ctrl+O`, `Enter`, `Ctrl+X`).

2.  **Activate Site**:
    ```bash
    sudo ln -s /etc/nginx/sites-available/t3-backend /etc/nginx/sites-enabled/
    sudo rm /etc/nginx/sites-enabled/default
    sudo nginx -t
    sudo systemctl restart nginx
    ```

## ✅ Finished!

Open your browser and verify:
`http://YOUR_EC2_PUBLIC_IP/health`

It should say `{"status": "healthy", ...}`.

---

# Troubleshooting

## 502 Bad Gateway
A **502 Bad Gateway** means Nginx is working, but your Backend has crashed.

### 1. Check Status
```bash
sudo systemctl status t3-backend
```
If it says **failed**, check the logs.

### 2. Read Errors
```bash
sudo journalctl -u t3-backend -n 50 --no-pager
```

### Common Fixes
1.  **Missing Dependencies**: If you see `ModuleNotFoundError`, run:
    ```bash
    uv add <missing-package-name>
    # OR if you updated pyproject.toml locally
    git pull
    uv sync
    ```
2.  **Missing Environment Variables**: Ensure `.env` has all keys.
3.  **MongoDB Connection**: If `connection refused`, ensure Docker container is running:
    ```bash
    docker start mongodb
    ```
