# iFrame Integration Guide

## Quick Start

Embed AgustoGPT in your application by passing the JWT token via URL query parameter.

### Basic iFrame Code

```html
<iframe 
  src="https://agustogpt.agusto.com/?jwt_token=YOUR_JWT_TOKEN_HERE"
  width="100%" 
  height="800px"
  frameborder="0"
  allow="clipboard-write">
</iframe>
```

---

## Dynamic Token Injection

### JavaScript Example

```html
<iframe 
  id="agustogpt-iframe"
  width="100%" 
  height="800px"
  allow="clipboard-write">
</iframe>

<script>
// Get JWT token from your authentication system
function getJWTToken() {
    // Replace with your actual token retrieval logic
    return localStorage.getItem('jwt_token') || 
           sessionStorage.getItem('jwt_token') ||
           getCookieValue('jwt_token');
}

// Load iframe with token
const iframe = document.getElementById('agustogpt-iframe');
const jwtToken = getJWTToken();

if (jwtToken) {
    iframe.src = `https://agustogpt.agusto.com/?jwt_token=${encodeURIComponent(jwtToken)}`;
} else {
    console.error('No JWT token available');
    iframe.src = 'https://agustogpt.agusto.com/'; // Loads as default_user
}
</script>
```

---

## Framework Integration

### React

```jsx
import React, { useContext } from 'react';
import { AuthContext } from './AuthContext'; // Your auth context

function AgustoGPTWidget() {
    const { jwtToken } = useContext(AuthContext);
    const iframeSrc = jwtToken 
        ? `https://agustogpt.agusto.com/?jwt_token=${encodeURIComponent(jwtToken)}`
        : 'https://agustogpt.agusto.com/';
    
    return (
        <div style={{ width: '100%', height: '800px' }}>
            <iframe
                src={iframeSrc}
                width="100%"
                height="100%"
                frameBorder="0"
                allow="clipboard-write"
                title="AgustoGPT AI Assistant"
            />
        </div>
    );
}

export default AgustoGPTWidget;
```

### Angular

```typescript
import { Component, Input } from '@angular/core';
import { AuthService } from './auth.service'; // Your auth service

@Component({
  selector: 'app-agustogpt',
  template: `
    <iframe 
      [src]="iframeSrc | safe"
      width="100%" 
      height="800px"
      frameborder="0"
      allow="clipboard-write">
    </iframe>
  `
})
export class AgustoGPTComponent {
  iframeSrc: string;
  
  constructor(private authService: AuthService) {
    const token = this.authService.getToken();
    this.iframeSrc = token 
      ? `https://agustogpt.agusto.com/?jwt_token=${encodeURIComponent(token)}`
      : 'https://agustogpt.agusto.com/';
  }
}
```

### Vue.js

```vue
<template>
  <iframe
    :src="iframeSrc"
    width="100%"
    height="800px"
    frameborder="0"
    allow="clipboard-write"
  ></iframe>
</template>

<script>
export default {
  name: 'AgustoGPTEmbed',
  data() {
    return {
      jwtToken: this.$store.state.auth.token // From Vuex store
    }
  },
  computed: {
    iframeSrc() {
      return this.jwtToken
        ? `https://agustogpt.agusto.com/?jwt_token=${encodeURIComponent(this.jwtToken)}`
        : 'https://agustogpt.agusto.com/';
    }
  }
}
</script>
```

---

## How It Works

### 1. Parent Page Embeds iFrame

```html
<iframe src="https://agustogpt.agusto.com/?jwt_token=abc123..."></iframe>
```

### 2. AgustoGPT Reads URL Parameter

The Streamlit app automatically checks for `jwt_token` in the URL:

```python
# In get_jwt_token() function
query_params = st.query_params
if 'jwt_token' in query_params:
    return query_params['jwt_token']
```

### 3. Token Sent to Client API

```python
# Token is used to authenticate
GET https://ami-be.ag-apps.agusto.com/api/current-client
Authorization: Bearer <jwt_token_from_url>
```

### 4. User Data Retrieved

```json
{
  "id": "69172dff1998f58c40007180",
  "company": "GPT",
  "country": "Nigeria",
  "industryReports": [...]
}
```

### 5. UI Updates with User Info

The sidebar displays:
- User ID
- Company name
- Available reports count

---

## Testing

### Local Testing

1. **Start AgustoGPT:**
   ```bash
   streamlit run main.py
   ```

2. **Open test file in browser:**
   ```bash
   # Open test_iframe_integration.html in your browser
   open test_iframe_integration.html  # macOS
   start test_iframe_integration.html  # Windows
   ```

3. **Enter your JWT token and click "Load with Token"**

### Direct URL Testing

Test without iframe first:
```
http://localhost:8501/?jwt_token=YOUR_JWT_TOKEN_HERE
```

Check the sidebar:
- ✅ Should show your actual user ID (not "default_user")
- ✅ Should show your company name
- ✅ Should show your available reports

---

## Token Refresh

### Scenario: JWT Token Expires

When the JWT token expires (typically 1-2 hours), you need to refresh the iframe:

```javascript
function refreshAgustoGPTWithNewToken(newJwtToken) {
    const iframe = document.getElementById('agustogpt-iframe');
    const timestamp = new Date().getTime();
    
    // Reload iframe with new token
    iframe.src = `https://agustogpt.agusto.com/?jwt_token=${encodeURIComponent(newJwtToken)}&_t=${timestamp}`;
}

// Listen for token refresh events in your app
window.addEventListener('token-refreshed', function(event) {
    refreshAgustoGPTWithNewToken(event.detail.newToken);
});
```

---

## Security Best Practices

### ✅ DO:

1. **Use HTTPS in production:**
   ```html
   <iframe src="https://agustogpt.agusto.com/?jwt_token=..."></iframe>
   ```

2. **Encode the token:**
   ```javascript
   const encoded = encodeURIComponent(jwtToken);
   ```

3. **Use short-lived tokens** (1-2 hour expiration)

4. **Implement token refresh** mechanism

5. **Set proper CORS and CSP headers** on your Streamlit server

### ❌ DON'T:

1. **Don't hardcode tokens** in HTML files committed to git
2. **Don't use HTTP** in production (tokens will be visible in network traffic)
3. **Don't use long-lived tokens** (increases security risk)
4. **Don't log URLs** with tokens on the server
5. **Don't share tokens** between different users

---

## Troubleshooting

### Issue: "default_user" still showing

**Possible causes:**
1. Token not being passed correctly
2. Token is invalid or expired
3. URL parameter not being read

**Debug steps:**
1. Enable debug mode: Add `?jwt_token=YOUR_TOKEN&embed=true` to URL
2. Check browser console for errors
3. In AgustoGPT, enable `DEBUG_COOKIES=true` in `.env`
4. Look for: `🔗 Using JWT from URL parameter (iframe)` in sidebar

### Issue: iframe not loading

**Solutions:**
1. Check CORS settings on Streamlit server
2. Verify iframe `allow` attribute includes necessary permissions
3. Check browser console for CSP errors
4. Ensure `X-Frame-Options` header allows embedding

### Issue: Token visible in browser history

**Mitigation:**
1. Use short-lived tokens
2. Implement token rotation
3. Clear URL after loading (advanced):
   ```javascript
   // After iframe loads, clean up URL
   setTimeout(() => {
       history.replaceState({}, '', window.location.pathname);
   }, 1000);
   ```

---

## Advanced: Token from Multiple Sources

Handle different scenarios:

```javascript
function getJWTTokenForIframe() {
    // Priority 1: Fresh token from auth service
    if (window.authService && window.authService.isAuthenticated()) {
        return window.authService.getToken();
    }
    
    // Priority 2: From localStorage
    const storedToken = localStorage.getItem('jwt_token');
    if (storedToken && !isTokenExpired(storedToken)) {
        return storedToken;
    }
    
    // Priority 3: From cookie
    const cookieToken = getCookieValue('jwt_token');
    if (cookieToken) {
        return cookieToken;
    }
    
    // No token available
    console.warn('No valid JWT token found');
    return null;
}

function isTokenExpired(token) {
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        return payload.exp * 1000 < Date.now();
    } catch (e) {
        return true;
    }
}

function getCookieValue(name) {
    const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    return match ? match[2] : null;
}

// Use it
const iframe = document.getElementById('agustogpt-iframe');
const token = getJWTTokenForIframe();
if (token) {
    iframe.src = `https://agustogpt.agusto.com/?jwt_token=${encodeURIComponent(token)}`;
}
```

---

## Production Checklist

Before deploying:

- [ ] Use HTTPS for both parent and iframe
- [ ] Implement JWT token refresh mechanism
- [ ] Set appropriate token expiration (1-2 hours)
- [ ] Configure CSP headers
- [ ] Test token expiration handling
- [ ] Enable error monitoring
- [ ] Set up logging (without logging tokens)
- [ ] Test with real user accounts
- [ ] Verify fallback to default_user works gracefully
- [ ] Document token format for your team

---

## Support

For more information:
- `config_jwt_token.md` - Detailed JWT configuration
- `README.md` - General application setup
- `DEV_SETUP.md` - Development mode features
- `QUICK_START.md` - Quick setup guide

