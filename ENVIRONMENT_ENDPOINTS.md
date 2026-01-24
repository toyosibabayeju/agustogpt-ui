# Environment-Based API Endpoints

## Overview

AgustoGPT supports different client API endpoints for development and production environments, allowing you to test against a staging/test API without affecting production data.

---

## How It Works

The client API endpoint is automatically selected based on the `ENABLE_DEV_MODE` environment variable:

```python
# In main.py (lines 52-58)
if os.getenv('ENABLE_DEV_MODE', 'false').lower() == 'true':
    CLIENT_API_URL = 'https://ami-be.ag-test.agusto.com'
else:
    CLIENT_API_URL = 'https://ami-be.ag-apps.agusto.com'
```

---

## Configuration

### Development Mode (Testing)

Add to your `.env` file:

```bash
# Enable development mode
ENABLE_DEV_MODE=true

# Test/Staging endpoint (automatically used)
CLIENT_API_URL_DEV=https://ami-be.ag-test.agusto.com

# Production endpoint (ignored in dev mode)
CLIENT_API_URL=https://ami-be.ag-apps.agusto.com

# Show which endpoint is being used
DEBUG_COOKIES=true
```

**Result:**
- Uses: `https://ami-be.ag-test.agusto.com/api/current-client`
- Sidebar shows: `🌐 Using TEST client API`

### Production Mode

Add to your `.env` file:

```bash
# Disable development mode (or omit this line)
ENABLE_DEV_MODE=false

# Production endpoint (used)
CLIENT_API_URL=https://ami-be.ag-apps.agusto.com

# Test endpoint (ignored in production mode)
CLIENT_API_URL_DEV=https://ami-be.ag-test.agusto.com
```

**Result:**
- Uses: `https://ami-be.ag-apps.agusto.com/api/current-client`
- Sidebar shows: `🌐 Using PRODUCTION client API` (if debug enabled)

---

## Benefits

### ✅ For Development

1. **Safe testing**: Test against staging API without affecting production
2. **Faster iteration**: Use test data that's easier to manipulate
3. **Isolated environment**: Changes don't impact live users
4. **Debug features**: Additional tools enabled in dev mode

### ✅ For Production

1. **Secure**: Debug features disabled
2. **Stable**: Production API with production data
3. **Simple**: Just set `ENABLE_DEV_MODE=false`
4. **Clean**: No test data or debug messages

---

## Environment Variables

### Required for Both Modes

```bash
AGENT_API_URL=http://localhost:8000
```

### For Development

```bash
ENABLE_DEV_MODE=true
CLIENT_API_URL_DEV=https://ami-be.ag-test.agusto.com
DEBUG_COOKIES=true
DEBUG_QUERIES=true
JWT_TOKEN=your_test_jwt_token  # Optional fallback
```

### For Production

```bash
ENABLE_DEV_MODE=false
CLIENT_API_URL=https://ami-be.ag-apps.agusto.com
DEBUG_COOKIES=false
DEBUG_QUERIES=false
# JWT_TOKEN should be empty - use cookies only
```

---

## Debug Information

When `DEBUG_COOKIES=true`, the sidebar shows which endpoint is active:

**Development Mode:**
```
🌐 Using TEST client API: https://ami-be.ag-test.agusto.com
```

**Production Mode:**
```
🌐 Using PRODUCTION client API: https://ami-be.ag-apps.agusto.com
```

---

## API Endpoints Comparison

| Feature | Development | Production |
|---------|-------------|------------|
| **Base URL** | `ami-be.ag-test.agusto.com` | `ami-be.ag-apps.agusto.com` |
| **Purpose** | Testing, staging | Live production data |
| **Data** | Test users, sample reports | Real users, actual reports |
| **Debug Tools** | Enabled | Disabled |
| **Manual JWT Input** | Available | Hidden |
| **Environment Var** | `ENABLE_DEV_MODE=true` | `ENABLE_DEV_MODE=false` |

---

## Switching Between Modes

### Development to Production

1. Edit `.env`:
   ```bash
   ENABLE_DEV_MODE=false
   DEBUG_COOKIES=false
   DEBUG_QUERIES=false
   ```

2. Restart the app:
   ```bash
   streamlit run main.py
   ```

### Production to Development

1. Edit `.env`:
   ```bash
   ENABLE_DEV_MODE=true
   DEBUG_COOKIES=true
   DEBUG_QUERIES=true
   ```

2. Restart the app:
   ```bash
   streamlit run main.py
   ```

---

## Deployment

### Local Development

```bash
# .env
ENABLE_DEV_MODE=true
CLIENT_API_URL_DEV=https://ami-be.ag-test.agusto.com
```

### Staging/UAT

```bash
# .env
ENABLE_DEV_MODE=true  # Still use test endpoint
CLIENT_API_URL_DEV=https://ami-be.ag-test.agusto.com
DEBUG_COOKIES=false  # Disable debug in UAT
DEBUG_QUERIES=false
```

### Production

```bash
# .env
ENABLE_DEV_MODE=false
CLIENT_API_URL=https://ami-be.ag-apps.agusto.com
DEBUG_COOKIES=false
DEBUG_QUERIES=false
JWT_TOKEN=  # Empty - use cookies only
```

Or via environment variables in Azure/Docker:

```bash
docker run -e ENABLE_DEV_MODE=false \
           -e CLIENT_API_URL=https://ami-be.ag-apps.agusto.com \
           agustogpt-ui
```

---

## Testing the Configuration

### Verify Current Endpoint

1. Enable debug mode:
   ```bash
   DEBUG_COOKIES=true
   ```

2. Run the app and check the sidebar

3. Look for the endpoint indicator:
   - `🌐 Using TEST client API` = Development mode
   - `🌐 Using PRODUCTION client API` = Production mode

### Test API Connection

Try fetching user details manually:

**Development:**
```bash
curl -X GET https://ami-be.ag-test.agusto.com/api/current-client \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

**Production:**
```bash
curl -X GET https://ami-be.ag-apps.agusto.com/api/current-client \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

---

## Troubleshooting

### Issue: Wrong endpoint being used

**Solution:** Check your `.env` file for `ENABLE_DEV_MODE` value

### Issue: Can't connect to test API

**Solution:** Verify `CLIENT_API_URL_DEV` is set correctly and accessible

### Issue: Debug info not showing

**Solution:** Ensure `DEBUG_COOKIES=true` in `.env` and restart app

### Issue: Both endpoints failing

**Solutions:**
1. Check network connectivity
2. Verify JWT token is valid
3. Test endpoints with curl
4. Check firewall/VPN settings

---

## Best Practices

### ✅ DO:

- Use dev mode for local development and testing
- Use production mode for deployments
- Keep dev and prod endpoints configured
- Enable debug only in development
- Document which endpoint team members should use

### ❌ DON'T:

- Mix test and production data
- Use production endpoint for testing
- Enable debug modes in production
- Commit `.env` file with real tokens
- Use dev mode in production deployments

---

## Summary

| Setting | Development | Production |
|---------|-------------|------------|
| `ENABLE_DEV_MODE` | `true` | `false` |
| Client API | `ami-be.ag-test` | `ami-be.ag-apps` |
| Debug Info | Enabled | Disabled |
| Manual JWT Input | Visible | Hidden |
| Endpoint Shown | `🌐 TEST` | `🌐 PRODUCTION` |

This dual-endpoint configuration ensures safe development while maintaining production security!

