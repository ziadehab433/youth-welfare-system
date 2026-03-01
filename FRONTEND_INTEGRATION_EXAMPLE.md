# Frontend Integration Examples

## 🌐 How to Integrate Password Reset with Your Frontend

---

## React/Next.js Example

### 1. Request Password Reset Page

```jsx
// pages/forgot-password.jsx
import { useState } from 'react';
import axios from 'axios';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await axios.post(
        'http://localhost:8000/api/auth/password-reset/',
        { email }
      );
      
      setMessage(response.data.message);
    } catch (error) {
      setMessage('حدث خطأ. يرجى المحاولة مرة أخرى.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h1>نسيت كلمة المرور</h1>
      <form onSubmit={handleSubmit}>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="البريد الإلكتروني"
          required
        />
        <button type="submit" disabled={loading}>
          {loading ? 'جاري الإرسال...' : 'إرسال رابط إعادة التعيين'}
        </button>
      </form>
      {message && <p className="message">{message}</p>}
    </div>
  );
}
```

### 2. Reset Password Confirmation Page

```jsx
// pages/reset-password.jsx
import { useState } from 'react';
import { useRouter } from 'next/router';
import axios from 'axios';

export default function ResetPassword() {
  const router = useRouter();
  const { uid, token } = router.query;
  
  const [passwords, setPasswords] = useState({
    new_password: '',
    confirm_password: ''
  });
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.post(
        'http://localhost:8000/api/accounts/password-reset/confirm/',
        {
          uid,
          token,
          new_password: passwords.new_password,
          confirm_password: passwords.confirm_password
        }
      );
      
      setMessage(response.data.message);
      
      // Redirect to login after 2 seconds
      setTimeout(() => {
        router.push('/login');
      }, 2000);
      
    } catch (error) {
      setError(error.response?.data?.error || 'حدث خطأ');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h1>إعادة تعيين كلمة المرور</h1>
      <form onSubmit={handleSubmit}>
        <input
          type="password"
          value={passwords.new_password}
          onChange={(e) => setPasswords({...passwords, new_password: e.target.value})}
          placeholder="كلمة المرور الجديدة"
          required
        />
        <input
          type="password"
          value={passwords.confirm_password}
          onChange={(e) => setPasswords({...passwords, confirm_password: e.target.value})}
          placeholder="تأكيد كلمة المرور"
          required
        />
        <button type="submit" disabled={loading}>
          {loading ? 'جاري التحديث...' : 'تحديث كلمة المرور'}
        </button>
      </form>
      {message && <p className="success">{message}</p>}
      {error && <p className="error">{error}</p>}
    </div>
  );
}
```

---

## Vue.js Example

### 1. Request Password Reset Component

```vue
<!-- components/ForgotPassword.vue -->
<template>
  <div class="forgot-password">
    <h1>نسيت كلمة المرور</h1>
    <form @submit.prevent="handleSubmit">
      <input
        v-model="email"
        type="email"
        placeholder="البريد الإلكتروني"
        required
      />
      <button type="submit" :disabled="loading">
        {{ loading ? 'جاري الإرسال...' : 'إرسال رابط إعادة التعيين' }}
      </button>
    </form>
    <p v-if="message" class="message">{{ message }}</p>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      email: '',
      message: '',
      loading: false
    };
  },
  methods: {
    async handleSubmit() {
      this.loading = true;
      try {
        const response = await axios.post(
          'http://localhost:8000/api/auth/password-reset/',
          { email: this.email }
        );
        this.message = response.data.message;
      } catch (error) {
        this.message = 'حدث خطأ. يرجى المحاولة مرة أخرى.';
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>
```

### 2. Reset Password Component

```vue
<!-- components/ResetPassword.vue -->
<template>
  <div class="reset-password">
    <h1>إعادة تعيين كلمة المرور</h1>
    <form @submit.prevent="handleSubmit">
      <input
        v-model="newPassword"
        type="password"
        placeholder="كلمة المرور الجديدة"
        required
      />
      <input
        v-model="confirmPassword"
        type="password"
        placeholder="تأكيد كلمة المرور"
        required
      />
      <button type="submit" :disabled="loading">
        {{ loading ? 'جاري التحديث...' : 'تحديث كلمة المرور' }}
      </button>
    </form>
    <p v-if="message" class="success">{{ message }}</p>
    <p v-if="error" class="error">{{ error }}</p>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      newPassword: '',
      confirmPassword: '',
      message: '',
      error: '',
      loading: false
    };
  },
  methods: {
    async handleSubmit() {
      this.loading = true;
      this.error = '';
      
      const uid = this.$route.query.uid;
      const token = this.$route.query.token;
      
      try {
        const response = await axios.post(
          'http://localhost:8000/api/auth/password-reset/confirm/',
          {
            uid,
            token,
            new_password: this.newPassword,
            confirm_password: this.confirmPassword
          }
        );
        
        this.message = response.data.message;
        
        // Redirect to login after 2 seconds
        setTimeout(() => {
          this.$router.push('/login');
        }, 2000);
        
      } catch (error) {
        this.error = error.response?.data?.error || 'حدث خطأ';
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>
```

---

## Vanilla JavaScript Example

### Request Password Reset

```html
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <title>نسيت كلمة المرور</title>
</head>
<body>
    <h1>نسيت كلمة المرور</h1>
    <form id="forgotPasswordForm">
        <input type="email" id="email" placeholder="البريد الإلكتروني" required>
        <button type="submit">إرسال رابط إعادة التعيين</button>
    </form>
    <p id="message"></p>

    <script>
        document.getElementById('forgotPasswordForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            const messageEl = document.getElementById('message');
            
            try {
                const response = await fetch('http://localhost:8000/api/auth/password-reset/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ email })
                });
                
                const data = await response.json();
                messageEl.textContent = data.message;
                messageEl.style.color = 'green';
            } catch (error) {
                messageEl.textContent = 'حدث خطأ. يرجى المحاولة مرة أخرى.';
                messageEl.style.color = 'red';
            }
        });
    </script>
</body>
</html>
```

### Reset Password Confirmation

```html
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <title>إعادة تعيين كلمة المرور</title>
</head>
<body>
    <h1>إعادة تعيين كلمة المرور</h1>
    <form id="resetPasswordForm">
        <input type="password" id="newPassword" placeholder="كلمة المرور الجديدة" required>
        <input type="password" id="confirmPassword" placeholder="تأكيد كلمة المرور" required>
        <button type="submit">تحديث كلمة المرور</button>
    </form>
    <p id="message"></p>

    <script>
        // Get uid and token from URL
        const urlParams = new URLSearchParams(window.location.search);
        const uid = urlParams.get('uid');
        const token = urlParams.get('token');

        document.getElementById('resetPasswordForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const newPassword = document.getElementById('newPassword').value;
            const confirmPassword = document.getElementById('confirmPassword').value;
            const messageEl = document.getElementById('message');
            
            try {
                const response = await fetch('http://localhost:8000/api/auth/password-reset/confirm/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        uid,
                        token,
                        new_password: newPassword,
                        confirm_password: confirmPassword
                    })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    messageEl.textContent = data.message;
                    messageEl.style.color = 'green';
                    
                    // Redirect to login after 2 seconds
                    setTimeout(() => {
                        window.location.href = '/login';
                    }, 2000);
                } else {
                    messageEl.textContent = data.error || 'حدث خطأ';
                    messageEl.style.color = 'red';
                }
            } catch (error) {
                messageEl.textContent = 'حدث خطأ. يرجى المحاولة مرة أخرى.';
                messageEl.style.color = 'red';
            }
        });
    </script>
</body>
</html>
```

---

## 🔗 Email Link Handling

The email contains a link like:
```
http://localhost:8000/api/accounts/password-reset/confirm/?uid=c3R1ZGVudDoxMjM&token=abc123-xyz
```

### Option 1: Backend Handles Everything (Current Implementation)
Users click the link and Django serves a form page.

### Option 2: Redirect to Frontend
Modify the email template to point to your frontend:

```html
<!-- In email_body.html -->
<a href="http://localhost:3000/reset-password?uid={{ uid }}&token={{ token }}">
    إعادة تعيين كلمة المرور
</a>
```

Then your frontend extracts `uid` and `token` from the URL and calls the API.

---

## 🎨 Styling Example (CSS)

```css
.container {
  max-width: 400px;
  margin: 50px auto;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

h1 {
  text-align: center;
  color: #333;
  margin-bottom: 30px;
}

form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

input {
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
}

button {
  padding: 12px;
  background-color: #667eea;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.3s;
}

button:hover {
  background-color: #5568d3;
}

button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.message, .success {
  padding: 10px;
  background-color: #d4edda;
  color: #155724;
  border-radius: 4px;
  text-align: center;
}

.error {
  padding: 10px;
  background-color: #f8d7da;
  color: #721c24;
  border-radius: 4px;
  text-align: center;
}
```

---

## 🔐 Security Best Practices

1. **Always use HTTPS in production**
2. **Validate passwords on frontend before sending**
3. **Show loading states to prevent double submissions**
4. **Clear sensitive data from memory after use**
5. **Implement rate limiting on frontend**
6. **Don't expose detailed error messages**

---

## 📱 Mobile App Integration (React Native)

```javascript
import axios from 'axios';

// Request password reset
const requestPasswordReset = async (email) => {
  try {
    const response = await axios.post(
      'http://your-api.com/api/auth/password-reset/',
      { email }
    );
    return { success: true, message: response.data.message };
  } catch (error) {
    return { success: false, message: 'حدث خطأ' };
  }
};

// Confirm password reset
const confirmPasswordReset = async (uid, token, newPassword, confirmPassword) => {
  try {
    const response = await axios.post(
      'http://your-api.com/api/auth/password-reset/confirm/',
      {
        uid,
        token,
        new_password: newPassword,
        confirm_password: confirmPassword
      }
    );
    return { success: true, message: response.data.message };
  } catch (error) {
    return { 
      success: false, 
      message: error.response?.data?.error || 'حدث خطأ' 
    };
  }
};
```

---

## 🧪 Testing Frontend Integration

1. **Test with valid email**
2. **Test with invalid email**
3. **Test password mismatch**
4. **Test weak passwords**
5. **Test expired tokens**
6. **Test network errors**
7. **Test loading states**
8. **Test redirect after success**

---

## 📞 Need Help?

Refer to:
- `PASSWORD_RESET_SETUP.md` - Backend setup
- `API_QUICK_REFERENCE.md` - API documentation
- Django CORS settings if frontend is on different domain

---

**Note:** Remember to update CORS settings in Django if your frontend is on a different domain!
