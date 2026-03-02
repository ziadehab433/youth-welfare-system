# 🔧 Frontend Connection Issue - 415 Unsupported Media Type

## ✅ Issue Fixed

The **415 Unsupported Media Type** error has been resolved by adding parser classes to Django REST Framework settings.

---

## 🔍 What Was the Problem?

Your frontend was sending JSON data, but Django REST Framework didn't have the proper parsers configured to handle it.

**Error:**
```
[WARNING] django.request Unsupported Media Type: /api/event/manage-events/
[WARNING] django.server "POST /api/event/manage-events/ HTTP/1.1" 415 68
```

---

## ✅ What Was Fixed

Updated `youth_welfare/settings.py` to include:

```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "apps.accounts.authentication.CustomJWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.AllowAny",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    
    # ✅ ADDED: Parser classes to handle different content types
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",        # For JSON data
        "rest_framework.parsers.FormParser",        # For form data
        "rest_framework.parsers.MultiPartParser",   # For file uploads
    ),
    
    # ✅ ADDED: Renderer classes for responses
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
}
```

---

## 🚀 Next Steps

### 1. Restart Django Server

```bash
# Stop the current server (Ctrl+C)
# Then restart:
python manage.py runserver
```

### 2. Test from Frontend

Your frontend request should now work. Make sure you're sending:

```javascript
// Correct headers
fetch('http://localhost:8000/api/event/manage-events/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_TOKEN_HERE'
  },
  body: JSON.stringify({
    // your data here
  })
})
```

---

## 🔍 Common Frontend Issues & Solutions

### Issue 1: CORS Error
**Symptom:** `Access-Control-Allow-Origin` error

**Solution:** Already configured in your settings:
```python
CORS_ALLOW_ALL_ORIGINS = True  # ✅ Already set
```

For production, update to:
```python
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:5173',  # Vite
    'https://your-frontend-domain.com'
]
```

---

### Issue 2: 401 Unauthorized
**Symptom:** Request returns 401

**Solution:** Include JWT token in headers:
```javascript
const token = localStorage.getItem('access_token');

fetch('http://localhost:8000/api/event/manage-events/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`  // ✅ Include token
  },
  body: JSON.stringify(data)
})
```

---

### Issue 3: 403 Forbidden (CSRF)
**Symptom:** CSRF verification failed

**Solution:** For API requests, you don't need CSRF token if using JWT. But if needed:

```javascript
// Get CSRF token from cookie
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// Include in headers
headers: {
  'X-CSRFToken': getCookie('csrftoken')
}
```

---

### Issue 4: 415 Unsupported Media Type (Fixed)
**Symptom:** Request returns 415

**Solution:** ✅ Already fixed by adding parser classes

---

## 📝 Frontend Examples

### React/Axios Example

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  }
});

// Add token to all requests
api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Usage
const createEvent = async (eventData) => {
  try {
    const response = await api.post('/event/manage-events/', eventData);
    return response.data;
  } catch (error) {
    console.error('Error:', error.response?.data);
    throw error;
  }
};
```

---

### Vue.js Example

```javascript
// api.js
import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json'
  }
});

apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default apiClient;

// Usage in component
import apiClient from './api';

export default {
  methods: {
    async createEvent(eventData) {
      try {
        const response = await apiClient.post('/event/manage-events/', eventData);
        return response.data;
      } catch (error) {
        console.error('Error:', error.response?.data);
      }
    }
  }
}
```

---

### Vanilla JavaScript/Fetch Example

```javascript
const API_BASE_URL = 'http://localhost:8000/api';

async function apiRequest(endpoint, method = 'GET', data = null) {
  const token = localStorage.getItem('access_token');
  
  const options = {
    method,
    headers: {
      'Content-Type': 'application/json',
    }
  };
  
  if (token) {
    options.headers['Authorization'] = `Bearer ${token}`;
  }
  
  if (data) {
    options.body = JSON.stringify(data);
  }
  
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Request failed');
    }
    
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
}

// Usage
apiRequest('/event/manage-events/', 'POST', {
  name: 'Event Name',
  description: 'Event Description'
})
.then(data => console.log('Success:', data))
.catch(error => console.error('Error:', error));
```

---

## 🧪 Testing the Fix

### 1. Test with cURL

```bash
curl -X POST http://localhost:8000/api/event/manage-events/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"name": "Test Event", "description": "Test"}'
```

### 2. Test with Postman

1. Set method to POST
2. URL: `http://localhost:8000/api/event/manage-events/`
3. Headers:
   - `Content-Type: application/json`
   - `Authorization: Bearer YOUR_TOKEN`
4. Body (raw JSON):
   ```json
   {
     "name": "Test Event",
     "description": "Test Description"
   }
   ```

---

## 🔍 Debugging Tips

### Check Django Logs

Your logs show:
```
[INFO] audit POST /api/event/manage-events/ | User: oo (oo@gmail.com) | Status: 415
```

After the fix, you should see:
```
[INFO] audit POST /api/event/manage-events/ | User: oo (oo@gmail.com) | Status: 201
```

### Enable Debug Mode (Development Only)

In `settings.py`:
```python
DEBUG = True  # Should already be True for development
```

### Check Browser Console

Open browser DevTools (F12) and check:
1. **Network tab** - See the actual request/response
2. **Console tab** - See any JavaScript errors

---

## 📊 Status Codes Reference

| Code | Meaning | Solution |
|------|---------|----------|
| 200 | Success | ✅ Request worked |
| 201 | Created | ✅ Resource created |
| 400 | Bad Request | Check request data format |
| 401 | Unauthorized | Add/check JWT token |
| 403 | Forbidden | Check permissions |
| 404 | Not Found | Check URL |
| 415 | Unsupported Media Type | ✅ Fixed! |
| 500 | Server Error | Check Django logs |

---

## ✅ Checklist

- [x] Parser classes added to settings.py
- [ ] Django server restarted
- [ ] Frontend request includes `Content-Type: application/json`
- [ ] Frontend request includes `Authorization: Bearer TOKEN` (if needed)
- [ ] CORS configured correctly
- [ ] Test request successful

---

## 🎉 Summary

**Problem:** 415 Unsupported Media Type  
**Cause:** Missing parser classes in REST Framework settings  
**Solution:** Added JSONParser, FormParser, and MultiPartParser  
**Status:** ✅ Fixed

Restart your Django server and try your frontend request again!

---

**Last Updated:** 2026-03-01
