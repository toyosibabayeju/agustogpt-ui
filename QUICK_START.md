# Quick Start - Testing JWT Authentication

## Easiest Way to Test JWT Token (Manual Input)

1. **Create or edit your `.env` file**:
   ```bash
   ENABLE_DEV_MODE=true
   DEBUG_COOKIES=true
   AGENT_API_URL=http://localhost:8000
   CLIENT_API_URL=https://ami-be.ag-apps.agusto.com
   ```

2. **Run the application**:
   ```bash
   streamlit run main.py
   ```

3. **Look in the sidebar** - scroll to the bottom

4. **You'll see "🔧 Development Mode"** section

5. **Click "Manual JWT Token" to expand**

6. **Paste your JWT token** in the text area

7. **Click "Set Token"**

8. **The app will reload** and fetch your user details from the API

## Example JWT Token (For Testing Mock)

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNjkxNzJkZmYxOTk4ZjU4YzQwMDA3MTgwIiwidXNlcm5hbWUiOiJ2aXB1bCBrdW1hciIsImNvbXBhbnkiOiJHUFQiLCJjb3VudHJ5IjoiTmlnZXJpYSIsImVtYWlsIjoidmlwdWwua3VtYXJAZXhhbXBsZS5jb20iLCJpYXQiOjE3MzIwNTAwMDAsImV4cCI6MTczMjEzNjQwMH0.ZXhhbXBsZV9zaWduYXR1cmVfZm9yX3Rlc3RpbmdfcHVycG9zZXM
```

⚠️ **Note**: This is a MOCK token. It won't authenticate with your real API. Get a real token from your authentication system.

## What You'll See

With `DEBUG_COOKIES=true`, the sidebar will show:
- 🔍 Available cookies
- Where the JWT token is coming from
- Any errors reading cookies

## Alternative: Use Environment Variable

Instead of manual input, you can also add to `.env`:
```bash
JWT_TOKEN=your_real_jwt_token_here
```

## Need a Real Token?

Get it from your login system or by calling:
```bash
curl -X POST https://ami-be.ag-apps.agusto.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'
```

## Troubleshooting

**Still showing "default_user"?**
- Make sure `ENABLE_DEV_MODE=true` is in your `.env`
- Check the sidebar for the Development Mode section
- Try setting `DEBUG_COOKIES=true` to see what's happening
- Verify your JWT token is valid and not expired

For more details, see `DEV_SETUP.md`

