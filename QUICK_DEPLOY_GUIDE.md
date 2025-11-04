# Quick Deployment Guide

## 🚀 Deploy to Render in 3 Steps

### Step 1: Commit and Push Changes
```bash
git add .
git commit -m "Fix database schema and auth responses for deployment"
git push origin main
```

### Step 2: Render Will Auto-Deploy
- Render detects the push and starts deployment
- Uses `render.yaml` configuration
- Runs: `pip install -r requirements.txt && python migrate.py`
- Starts: `gunicorn run:app`

### Step 3: Verify Deployment
Test registration endpoint:
```bash
curl -X POST https://workforce-backend-kfxw.onrender.com/api/auth/register/client \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "password123",
    "company_name": "Test Company"
  }'
```

Expected response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1Qi...",
  "refresh_token": "eyJ0eXAiOiJKV1Qi...",
  "user": {
    "id": 1,
    "email": "newuser@example.com",
    "role": "client",
    "created_at": "2025-11-03T21:00:00.000000"
  }
}
```

## ✅ What Was Fixed

1. **Database Schema** - Added missing `verification_token` and `token_expires_at` columns
2. **Migration Script** - Enhanced to auto-patch schema on deployment
3. **Auth Responses** - Now include user data (id, email, role) for frontend routing
4. **Deployment Config** - Created `render.yaml` for proper build process

## 🎯 Frontend Integration

Update your frontend auth handlers to use the new response format:

```javascript
// After successful registration or login
const handleAuthSuccess = (response) => {
  const { access_token, refresh_token, user } = response;
  
  // Store tokens and user data
  localStorage.setItem('access_token', access_token);
  localStorage.setItem('refresh_token', refresh_token);
  localStorage.setItem('user', JSON.stringify(user));
  
  // Redirect based on role
  switch(user.role) {
    case 'client':
      navigate('/client/dashboard');
      break;
    case 'freelancer':
      navigate('/freelancer/dashboard');
      break;
    case 'admin':
      navigate('/admin/dashboard');
      break;
    default:
      navigate('/');
  }
};

// Use it in your registration/login handlers
const handleRegister = async (formData) => {
  try {
    const response = await fetch('https://workforce-backend-kfxw.onrender.com/api/auth/register/client', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData)
    });
    
    if (response.ok) {
      const data = await response.json();
      handleAuthSuccess(data);
    } else {
      const error = await response.json();
      console.error('Registration failed:', error);
    }
  } catch (error) {
    console.error('Network error:', error);
  }
};
```

## 🔍 Troubleshooting

### If deployment fails:
1. Check Render logs for specific errors
2. Verify DATABASE_URL is set in Render environment variables
3. Ensure all files are committed and pushed

### If "column does not exist" error persists:
The migration script has auto-patching. If it still fails, manually run in Render shell:
```sql
ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_token VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS token_expires_at TIMESTAMP;
```

### If registration works but frontend doesn't redirect:
1. Check browser console for errors
2. Verify the response includes the `user` object
3. Check your frontend routing logic

## 📝 Environment Variables on Render

Make sure these are set in your Render dashboard:
- ✅ `DATABASE_URL` (auto-set by Render)
- ✅ `SECRET_KEY` (your Flask secret)
- ✅ `JWT_SECRET_KEY` (your JWT secret)
- ✅ `AUTO_CREATE_TABLES=true`
- ✅ `AUTO_PATCH_SCHEMA=true`
- ✅ `FLASK_ENV=production`

Optional (if using):
- `SENDGRID_API_KEY`
- `CLOUDINARY_URL`
- `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`

## 🎉 Success Indicators

✅ Deployment completes without errors
✅ Registration endpoint returns 201 with user data
✅ Login endpoint returns 200 with user data
✅ Frontend redirects users to correct dashboard
✅ No "column does not exist" errors in logs

## 📚 Additional Resources

- Full details: See `DEPLOYMENT_FIX.md`
- Test locally: Run `python test_auth_response.py`
- Verify schema: Run `python verify_schema.py`
- Commit message: See `COMMIT_MESSAGE.txt`

