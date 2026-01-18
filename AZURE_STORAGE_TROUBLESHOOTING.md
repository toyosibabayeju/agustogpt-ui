# Azure Storage Troubleshooting Guide

## Problem: Chat History Not Working

If your Azure chat history storage is not working, follow these steps to diagnose and fix the issue.

---

## Step 1: Check Prerequisites

### Required Azure Packages

The app requires these Python packages:

```bash
pip install azure-storage-blob azure-data-tables
```

**Verify installation:**
```bash
pip list | grep azure
```

You should see:
- `azure-storage-blob`
- `azure-data-tables`
- `azure-core`

---

## Step 2: Configure Environment Variables

### Required Settings in `.env`

```bash
# Azure Storage connection string (REQUIRED)
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=youraccountname;AccountKey=yourkey;EndpointSuffix=core.windows.net

# Optional (defaults will be used if not set)
AZURE_BLOB_CONTAINER_NAME=agustogpt-chats
AZURE_TABLE_NAME=AgustoGPTChats
```

### Get Your Connection String

1. Go to **Azure Portal** (portal.azure.com)
2. Navigate to your **Storage Account**
3. Click **Access Keys** in the left menu
4. Copy the **Connection String** from Key1 or Key2
5. Paste it into your `.env` file

---

## Step 3: Use Built-in Diagnostics

### Enable Development Mode

Add to your `.env`:
```bash
ENABLE_DEV_MODE=true
```

### Run the App

```bash
streamlit run main.py
```

### Open Diagnostics Panel

1. Look for **"🔧 Development Mode"** in the sidebar
2. Expand **"☁️ Azure Storage Diagnostics"**
3. Review the diagnostic information

### What to Look For

#### ✅ **Successful Configuration**
```
✅ Azure packages installed
Storage Manager Enabled: True
Session Storage Enabled: True
✅ Connection string found (XXX chars)
Storage User ID: GPT
Blob Container: agustogpt-chats
Table Name: AgustoGPTChats
Loaded Chats: 5
```

#### ❌ **Common Issues**

**Issue 1: Azure Packages Not Installed**
```
❌ Azure packages NOT installed: No module named 'azure'
```
**Fix:**
```bash
pip install azure-storage-blob azure-data-tables
```

**Issue 2: Connection String Missing**
```
Storage Manager Enabled: False
❌ AZURE_STORAGE_CONNECTION_STRING not set in .env
```
**Fix:** Add connection string to `.env` file

**Issue 3: Storage User ID Not Set**
```
⚠️ storage_user_id not set in session state
```
**Fix:** Restart the app - this is now auto-fixed by the safeguard

---

## Step 4: Test the Connection

Click the **"🔄 Test Azure Connection"** button in the diagnostics panel.

### Expected Results

**Success:**
```
✅ Connection successful! Found X chats
```

**Failure Examples:**

**Invalid Connection String:**
```
❌ Connection failed: The specified account is invalid
```
**Fix:** Verify your connection string is correct

**Network Issue:**
```
❌ Connection failed: Unable to connect to the remote server
```
**Fix:** Check firewall, proxy, or VPN settings

**Container Doesn't Exist:**
```
❌ Connection failed: The specified container does not exist
```
**Fix:** The app will auto-create containers, but check Azure portal for container status

---

## Step 5: Check Storage Status Indicator

Look for the storage status icon in the sidebar:

- **☁️ Green** = Azure storage is enabled and working
- **💾 Yellow** = Storage is disabled (using local session only)

---

## Step 6: Manual Testing

### Test with Azure Storage Explorer

1. Download **Azure Storage Explorer** (free)
2. Connect using your connection string
3. Navigate to:
   - **Blob Containers** → `agustogpt-chats`
   - **Tables** → `AgustoGPTChats`
4. Check if containers/tables exist and have data

### Test with Python Script

Create `test_azure.py`:

```python
import os
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from azure.data.tables import TableServiceClient

load_dotenv()

connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')

if not connection_string:
    print("❌ No connection string found")
    exit(1)

try:
    # Test Blob Service
    blob_client = BlobServiceClient.from_connection_string(connection_string)
    containers = list(blob_client.list_containers())
    print(f"✅ Blob connection successful! Found {len(containers)} containers")
    
    # Test Table Service
    table_client = TableServiceClient.from_connection_string(connection_string)
    tables = list(table_client.list_tables())
    print(f"✅ Table connection successful! Found {len(tables)} tables")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
```

Run:
```bash
python test_azure.py
```

---

## Common Issues & Solutions

### Issue: "Storage Manager Enabled: False"

**Causes:**
1. Azure packages not installed
2. Connection string missing or invalid
3. Initialization error

**Solutions:**
1. Install packages: `pip install azure-storage-blob azure-data-tables`
2. Set `AZURE_STORAGE_CONNECTION_STRING` in `.env`
3. Check app logs for error messages

---

### Issue: "No chat history available"

**Causes:**
1. No chats have been saved yet
2. Storage is disabled
3. Chats are stored under different user ID

**Solutions:**
1. Send a message to create a new chat (it auto-saves)
2. Verify storage is enabled (green cloud icon)
3. Check `storage_user_id` in diagnostics matches your company name

---

### Issue: Chats Not Saving

**Check:**
1. Look for save confirmation: "Chat saved to cloud ☁️" toast
2. If you see "Failed to save chat" ⚠️, check diagnostics
3. Verify you have write permissions on Azure Storage

**Debug:**
Check terminal/console for error messages like:
```
Failed to save chat session: AuthenticationFailed
```

---

### Issue: Chats From Before Company Name Change Not Showing

**Explanation:**
Chats are now stored by company name, not user ID.

**Previous chats** were stored under user IDs like:
- `69172dff1998f58c40007180/chat_xxx.json`

**New chats** are stored under company name:
- `GPT/chat_xxx.json`

**Solution:**
You can migrate old chats by:
1. Using Azure Storage Explorer
2. Moving blobs from old folder to company name folder
3. Updating Table Storage partition keys

---

## Testing Storage with New Chat

1. **Start a new chat** (click "New Chat" button)
2. **Send a message** (e.g., "What are the banking trends?")
3. **Check for toast notification**: "Chat saved to cloud ☁️"
4. **Refresh the page** (F5)
5. **Check "Chat History"** expander in sidebar
6. **Your chat should appear** in the list

---

## Storage Structure

### Blob Storage
```
Container: agustogpt-chats
├── GPT/
│   ├── chat_abc123_20251125120000.json
│   └── chat_def456_20251125130000.json
├── default_user/
│   └── chat_xyz789_20251125140000.json
└── logs/
    └── 20251125/
        └── chat_abc123_120000.json
```

### Table Storage
```
Table: AgustoGPTChats
PartitionKey (user_id) | RowKey (chat_id)      | ChatTitle           | MessageCount
-----------------------|------------------------|---------------------|-------------
GPT                    | chat_abc123_20251125   | What are trends?    | 4
GPT                    | chat_def456_20251125   | Banking analysis    | 6
default_user           | chat_xyz789_20251125   | Test query          | 2
```

---

## Still Not Working?

### Collect Diagnostic Info

1. Open diagnostics panel
2. Take a screenshot
3. Check browser console (F12) for JavaScript errors
4. Check terminal for Python errors

### Enable Logging

Add to `azure_storage.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

This will show detailed Azure SDK logs.

---

## Alternative: Disable Azure Storage

If you want to use the app without cloud storage:

1. **Don't set** `AZURE_STORAGE_CONNECTION_STRING` in `.env`
2. The app will use **session-only** storage
3. Chats are lost when you close the browser

**Note:** The app still works perfectly without Azure storage; you just can't persist chats across sessions.

---

## Summary Checklist

- [ ] Azure packages installed
- [ ] Connection string in `.env`
- [ ] Connection string is valid
- [ ] Diagnostics show "Storage Manager Enabled: True"
- [ ] Storage User ID is set (shows company name or "default_user")
- [ ] Test connection button succeeds
- [ ] Green cloud icon appears in sidebar
- [ ] Test message shows "Chat saved to cloud" toast
- [ ] Chat appears in Chat History after refresh

---

## Need Help?

- Check Azure Portal for storage account status
- Review Azure Storage documentation
- Verify network connectivity to Azure
- Check firewall/proxy settings
- Ensure Azure Storage account has proper permissions

