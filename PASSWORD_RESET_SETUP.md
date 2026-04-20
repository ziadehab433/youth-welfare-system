# Password Reset Feature - Setup & Testing Guide

## 🎯 Overview
Password reset functionality for Students and Admins (مشرف النظام only) with 20-minute token expiration.

---

## 📧 Email Configuration

### Option 1: Gmail SMTP (Recommended for Production)

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate App Password**:
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Copy the 16-character password

3. **Update .env file**:
```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=xxxx xxxx xxxx xxxx  # 16-char app password
DEFAULT_FROM_EMAIL=noreply@youth-welfare.edu
```

### Option 2: Console Backend (Development Only)

For testing without sending real emails:

```python
# In settings.py, temporarily change:
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

Emails will print to your console instead of being sent.

---

## 🚀 Testing the Feature

### 1. Start Django Server
```bash
python manage.py runserver
```

### 2. Test Password Reset Request

**Endpoint:** `POST /api/accounts/password-reset/`

**Request:**
```bash
curl -X POST http://localhost:8000/api/accounts/password-reset/ \
  -H "Content-Type: application/json" \
  -d '{"email": "student@example.com"}'
```

**Response:**
```json
{
  "message": "إذا كان البريد الإلكتروني موجودًا، سيتم إرسال رابط إعادة تعيين كلمة المرور"
}
```

### 3. Check Email

The user will receive an email with:
- Subject: "إعادة تعيين كلمة المرور - الإدارة العامة لرعاية الشباب"
- Reset link valid for 20 minutes
- Beautiful HTML template with Arabic/English text

**Email Link Format:**
```
http://localhost:8000/api/accounts/password-reset/confirm/?uid=c3R1ZGVudDoxMjM&token=abc123-xyz
```

### 4. Test Password Reset Confirmation

**Endpoint:** `POST /api/accounts/password-reset/confirm/`

**Request:**
```bash
curl -X POST http://localhost:8000/api/accounts/password-reset/confirm/ \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "c3R1ZGVudDoxMjM",
    "token": "abc123-token-xyz",
    "new_password": "NewSecurePass123!",
    "confirm_password": "NewSecurePass123!"
  }'
```

**Success Response:**
```json
{
  "message": "تم تغيير كلمة المرور بنجاح"
}
```

**Error Response (Invalid Token):**
```json
{
  "error": "رابط إعادة التعيين غير صالح أو منتهي الصلاحية"
}
```

---

## 🧪 Testing Scenarios

### Test Case 1: Valid Student Email
```bash
# Request reset
curl -X POST http://localhost:8000/api/accounts/password-reset/ \
  -H "Content-Type: application/json" \
  -d '{"email": "existing-student@example.com"}'

# Expected: Email sent, 200 OK
```

### Test Case 2: Valid Admin Email (مشرف النظام)
```bash
curl -X POST http://localhost:8000/api/accounts/password-reset/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com"}'

# Expected: Email sent, 200 OK
```

### Test Case 3: Non-existent Email
```bash
curl -X POST http://localhost:8000/api/accounts/password-reset/ \
  -H "Content-Type: application/json" \
  -d '{"email": "nonexistent@example.com"}'

# Expected: Same success message (security - no user enumeration)
```

### Test Case 4: Admin with Different Role
```bash
# Admin with role "مدير ادارة" should NOT receive reset email
curl -X POST http://localhost:8000/api/accounts/password-reset/ \
  -H "Content-Type: application/json" \
  -d '{"email": "dept-admin@example.com"}'

# Expected: Generic success message, no email sent
```

### Test Case 5: Expired Token (After 20 Minutes)
```bash
# Wait 20+ minutes after requesting reset, then try to confirm
curl -X POST http://localhost:8000/api/accounts/password-reset/confirm/ \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "...",
    "token": "...",
    "new_password": "NewPass123!",
    "confirm_password": "NewPass123!"
  }'

# Expected: 400 Bad Request - "رابط إعادة التعيين غير صالح أو منتهي الصلاحية"
```

### Test Case 6: Password Mismatch
```bash
curl -X POST http://localhost:8000/api/accounts/password-reset/confirm/ \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "...",
    "token": "...",
    "new_password": "NewPass123!",
    "confirm_password": "DifferentPass456!"
  }'

# Expected: 400 Bad Request - "كلمات المرور غير متطابقة"
```

### Test Case 7: Weak Password
```bash
curl -X POST http://localhost:8000/api/accounts/password-reset/confirm/ \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "...",
    "token": "...",
    "new_password": "123",
    "confirm_password": "123"
  }'

# Expected: 400 Bad Request - Django password validation errors
```

---

## 🔍 Swagger/OpenAPI Testing

1. Navigate to: `http://localhost:8000/api/schema/swagger-ui/`
2. Find "Password Reset" section
3. Test endpoints interactively

---

## 📊 Monitoring & Logs

Check logs for password reset activity:




```bash
# Application logs
tail -f logs/app.log

# Security logs
tail -f logs/security.log
```

**Log Messages:**
- `Password reset email sent to {email}` - Email sent successfully
- `Invalid or expired token for {user_type} {user_id}` - Token validation failed
- `Password reset successful for {user_type} {user_id}` - Password changed

---

## 🔒 Security Features

✅ **Token Expiration**: 20 minutes (configurable in settings.py)  
✅ **One-time Use**: Token invalidated after password change  
✅ **No User Enumeration**: Same response for existing/non-existing emails  
✅ **Password Validation**: Django's built-in validators  
✅ **Role-based Access**: Only students and "مشرف النظام" admins  
✅ **Separate Hashing**: bcrypt for students, Django hashers for admins  
✅ **HTTPS Recommended**: For production deployment  

---

## 🐛 Troubleshooting

### Issue: Emails Not Sending

**Check:**
1. Email credentials in .env are correct
2. Gmail App Password (not regular password)
3. Console output for error messages
4. Check logs/app.log for detailed errors

**Quick Test:**
```python
# In Django shell
python manage.py shell

from django.core.mail import send_mail
send_mail(
    'Test Subject',
    'Test message',
    'your-email@gmail.com',
    ['recipient@example.com'],
    fail_silently=False,
)
```

### Issue: Token Always Invalid

**Check:**
1. Token hasn't expired (20 minutes)
2. Password wasn't already changed (one-time use)
3. uid and token are correctly extracted from URL
4. User still exists in database

### Issue: Template Not Found

**Check:**
1. Templates directory exists: `apps/accounts/templates/password_reset/`
2. All 3 template files exist:
   - email_subject.txt
   - email_body.txt
   - email_body.html

---

## 📝 API Documentation

### Request Password Reset

**POST** `/api/accounts/password-reset/`

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response:** `200 OK`
```json
{
  "message": "إذا كان البريد الإلكتروني موجودًا، سيتم إرسال رابط إعادة تعيين كلمة المرور"
}
```

---

### Confirm Password Reset

**POST** `/api/accounts/password-reset/confirm/`

**Request Body:**
```json
{
  "uid": "c3R1ZGVudDoxMjM",
  "token": "abc123-token-xyz",
  "new_password": "NewSecurePass123!",
  "confirm_password": "NewSecurePass123!"
}
```

**Success Response:** `200 OK`
```json
{
  "message": "تم تغيير كلمة المرور بنجاح"
}
```

**Error Response:** `400 Bad Request`
```json
{
  "error": "رابط إعادة التعيين غير صالح أو منتهي الصلاحية"
}
```

---

## 🎨 Email Template Customization

Templates are located in: `apps/accounts/templates/password_reset/`

**Customize:**
- `email_subject.txt` - Email subject line
- `email_body.txt` - Plain text version
- `email_body.html` - HTML version (styled)

**Variables Available:**
- `{{ user_name }}` - User's name
- `{{ reset_url }}` - Password reset link
- `{{ expiry_minutes }}` - Token expiration time (20)

---

## 🚀 Production Deployment

### 1. Update Settings
```python
# settings.py
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com']
```

### 2. Use HTTPS
Ensure all URLs use HTTPS in production for security.

### 3. Email Service
Consider using:
- **SendGrid** (99% deliverability)
- **AWS SES** (cost-effective)
- **Mailgun** (developer-friendly)

### 4. Rate Limiting
Already configured in your middleware for auth endpoints.

---

## 📞 Support

For issues or questions:
1. Check logs: `logs/app.log` and `logs/security.log`
2. Review Django documentation: https://docs.djangoproject.com/en/stable/topics/email/
3. Test with console backend first before SMTP

---

## ✅ Checklist

- [ ] Email credentials configured in .env
- [ ] Gmail App Password generated (if using Gmail)
- [ ] Templates created in correct directory
- [ ] Server restarted after changes
- [ ] Test with valid student email
- [ ] Test with valid admin email (مشرف النظام)
- [ ] Test with invalid email
- [ ] Test token expiration (wait 20+ minutes)
- [ ] Test password validation
- [ ] Check email delivery
- [ ] Review logs for errors

---

**Feature Status:** ✅ Ready for Testing
**Last Updated:** 2026-03-01
