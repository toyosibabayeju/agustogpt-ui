# Development Setup Guide

## Development vs Production Endpoints

The application uses different client API endpoints based on the `ENABLE_DEV_MODE` setting:

- **Development Mode** (`ENABLE_DEV_MODE=true`): Uses `https://ami-be.ag-test.agusto.com`
- **Production Mode** (`ENABLE_DEV_MODE=false` or not set): Uses `https://ami-be.ag-apps.agusto.com`

This allows you to test against a test/staging environment without affecting production data.

## JWT Token Authentication for Development

Since the cookie manager may not work reliably when testing locally, we've added multiple ways to provide JWT tokens for development.

### Option 1: Manual JWT Token Input (Recommended for Local Testing)

1. **Enable Development Mode** in your `.env` file:
   ```bash
   ENABLE_DEV_MODE=true
   ```

2. **Run the main application**:
   ```bash
   streamlit run main.py
   ```

3. **In the sidebar**, you'll see a "🔧 Development Mode" section at the bottom

4. **Click on "Manual JWT Token" expander**

5. **Paste your JWT token** and click "Set Token"

6. The app will reload with your JWT token active

### Option 2: Environment Variable (Simple Fallback)

Add to your `.env` file:
```bash
JWT_TOKEN=your_jwt_token_here
```

The app will automatically use this if no manual token or cookie is found.

### Option 3: HTTP Cookies (Production Method)

This is how it works in production:
- Your authentication system sets a cookie named `jwt_token`
- The app automatically reads it
- For local testing with cookies, use `set_jwt_cookie.py`

### Testing with a Mock JWT Token

For testing purposes, you can use this mock JWT token:

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNjkxNzJkZmYxOTk4ZjU4YzQwMDA3MTgwIiwidXNlcm5hbWUiOiJ2aXB1bCBrdW1hciIsImNvbXBhbnkiOiJHUFQiLCJjb3VudHJ5IjoiTmlnZXJpYSIsImVtYWlsIjoidmlwdWwua3VtYXJAZXhhbXBsZS5jb20iLCJpYXQiOjE3MzIwNTAwMDAsImV4cCI6MTczMjEzNjQwMH0.ZXhhbXBsZV9zaWduYXR1cmVfZm9yX3Rlc3RpbmdfcHVycG9zZXM
```

**⚠️ Note**: This mock token won't work with your real API. You need a real JWT token from your authentication system.

## Getting a Real JWT Token

### Method 1: From Your Login System
If you have a login page, authenticate there and extract the JWT from:
- Browser cookies (F12 > Application > Cookies)
- LocalStorage
- Network tab (look for Authorization headers)

### Method 2: Via API Call
```bash
curl -X POST https://ami-be.ag-apps.agusto.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'
```

The response will contain your JWT token.

## Debug Mode

To see what's happening with cookies and tokens, enable debug mode:

Add to `.env`:
```bash
DEBUG_COOKIES=true
```

This will show in the sidebar:
- Available cookies
- Where the JWT token is coming from
- Cookie read errors (if any)

## Token Priority

The app checks for JWT tokens in this order:

1. **Manual Input** (Development Mode) - Highest priority
2. **HTTP Cookies** (`jwt_token` cookie)
3. **Environment Variable** (`JWT_TOKEN`)
4. **Default** - Falls back to "default_user"

## Troubleshooting

### Cookies not working between set_jwt_cookie.py and main.py

**Problem**: This is a known limitation - cookies set in one Streamlit app don't persist to another.

**Solution**: Use the Manual JWT Token Input (Option 1) instead.

### JWT token not being recognized

1. Enable `DEBUG_COOKIES=true` to see what's happening
2. Check if the token is properly formatted (starts with `eyJ`)
3. Verify the token hasn't expired
4. Try pasting it directly in the Manual JWT Token input

### "Failed to fetch client details" error

This means:
- The JWT token is invalid or expired
- The client API is not reachable
- The token doesn't have proper permissions

The app will fall back to "default_user" in this case.

## Production Deployment

**Important**: Before deploying to production:

1. Set `ENABLE_DEV_MODE=false` (or remove it entirely)
2. Set `DEBUG_COOKIES=false` (or remove it)
3. Ensure your authentication system properly sets the `jwt_token` cookie
4. Never commit real JWT tokens to version control
5. Do not deploy `set_jwt_cookie.py` to production

