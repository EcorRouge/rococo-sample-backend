# OAuth SSO Setup Guide for Rococo Sample App

This guide will help you set up Google and Microsoft OAuth Single Sign-On (SSO) for your Rococo Sample application.

## 🚀 **What's Been Implemented**

Your application now has:
- ✅ **Backend OAuth endpoints** (`/auth/google/exchange`, `/auth/microsoft/exchange`)
- ✅ **Frontend OAuth authentication service** with PKCE support
- ✅ **OAuth callback handling** and token exchange
- ✅ **Automatic user creation** for new OAuth users
- ✅ **Seamless login flow** for existing users

## 🔧 **Setup Steps**

### 1. **Google OAuth Setup**

#### A. Create Google OAuth App
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the **Google+ API** and **Google OAuth2 API**
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client IDs**
5. Choose **Web application**
6. Add authorized redirect URIs:
   - `http://localhost:3000/auth/callback` (for development)
   - `https://yourdomain.com/auth/callback` (for production)
7. Copy the **Client ID** and **Client Secret**

#### B. Configure Backend
Add to your `.env.secrets`:
```bash
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
```

#### C. Configure Frontend
Add to your `.env`:
```bash
VUE_APP_GOOGLE_CLIENT_ID=your_google_client_id_here
```

### 2. **Microsoft OAuth Setup**

#### A. Create Microsoft OAuth App
1. Go to [Azure Portal](https://portal.azure.com/)
2. Navigate to **Azure Active Directory** → **App registrations**
3. Click **New registration**
4. Fill in the details:
   - **Name**: Your app name
   - **Supported account types**: Choose based on your needs
   - **Redirect URI**: 
     - `http://localhost:3000/auth/callback` (for development)
     - `https://yourdomain.com/auth/callback` (for production)
5. After creation, go to **Certificates & secrets**
6. Create a new **Client secret** and copy it
7. Copy the **Application (client) ID**

#### B. Configure Backend
Add to your `.env.secrets`:
```bash
MICROSOFT_CLIENT_ID=your_microsoft_client_id_here
MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret_here
```

#### C. Configure Frontend
Add to your `.env`:
```bash
VUE_APP_MICROSOFT_CLIENT_ID=your_microsoft_client_id_here
```

## 🔄 **How OAuth Flow Works**

1. **User clicks OAuth button** → Redirects to Google/Microsoft
2. **User authenticates** → Google/Microsoft redirects back with authorization code
3. **Frontend receives code** → Sends to backend `/auth/{provider}/exchange`
4. **Backend exchanges code** → Gets access token from provider
5. **Backend gets user info** → Creates/updates user in database
6. **User is logged in** → Receives access token and user data

## 📁 **Files Modified/Added**

### Backend
- `common/services/oauth.py` - OAuth client service
- `common/services/auth.py` - Added OAuth login method
- `flask/app/views/auth.py` - Added OAuth exchange endpoints
- `common/app_config.py` - Added OAuth configuration
- `.env.secrets` - Added OAuth environment variables

### Frontend
- `src/services/auth.service.js` - OAuth authentication service
- `src/pages/Auth/AuthCallback.vue` - OAuth callback handler
- `src/pages/LoginPage.vue` - Added OAuth buttons
- `src/stores/auth.js` - Added OAuth methods
- `src/router/routes.js` - Added OAuth callback route
- `package.json` - Added OAuth dependencies
- `.env.example` - Added OAuth environment variables

## 🧪 **Testing OAuth**

### 1. **Start Backend**
```bash
cd rococo-sample-backend/flask
poetry install --no-root
poetry run python main.py
```

### 2. **Start Frontend**
```bash
cd rococo-sample-vue3
npm install
npm run dev
```

### 3. **Test OAuth Flow**
1. Go to `/login`
2. Click Google or Microsoft button
3. Complete OAuth flow
4. Verify user is created/logged in

## 🔒 **Security Features**

- **PKCE (Proof Key for Code Exchange)** - Prevents authorization code interception
- **Secure token storage** - Tokens stored in localStorage with proper cleanup
- **Error handling** - Comprehensive error handling for OAuth failures
- **User validation** - Email verification and user data validation

## 🚨 **Common Issues & Solutions**

### Issue: "Invalid redirect URI"
**Solution**: Ensure redirect URI in OAuth app matches exactly what's configured

### Issue: "Client ID not found"
**Solution**: Check environment variables are properly set and loaded

### Issue: "OAuth authentication failed"
**Solution**: Check backend logs for detailed error messages

### Issue: "PKCE code_verifier not found"
**Solution**: Clear browser storage and try again

## 📚 **Additional Resources**

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Microsoft OAuth 2.0 Documentation](https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-auth-code-flow)
- [OIDC Client TS Documentation](https://github.com/authts/oidc-client-ts)

## 🎯 **Next Steps**

1. **Set up OAuth apps** in Google Cloud Console and Azure Portal
2. **Configure environment variables** with your OAuth credentials
3. **Test the OAuth flow** in development
4. **Deploy to production** with proper production OAuth apps
5. **Monitor OAuth usage** and user creation

Your OAuth SSO implementation is now complete and ready for production use! 🎉
