# TASK_015: OAuth Authentication Implementation

## Status: PENDING

## Overview
Implement social login functionality to reduce signup friction and improve user experience. Start with Google OAuth and expand to other providers.

## Objectives
1. Set up OAuth provider configurations
2. Implement backend OAuth flow with FastAPI
3. Update frontend login/register pages
4. Handle account linking for existing users
5. Support multiple providers (Google, GitHub, Microsoft)

## Implementation Steps

### 1. Backend Dependencies
```bash
# Add to requirements.txt
authlib==1.2.1
httpx==0.24.1
# or
python-social-auth[fastapi]==5.3.0
```

### 2. OAuth Configuration
```python
# backend/app/core/config.py
class Settings(BaseSettings):
    # ... existing settings ...
    
    # OAuth Settings
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8001/auth/google/callback"
    
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    
    MICROSOFT_CLIENT_ID: str = ""
    MICROSOFT_CLIENT_SECRET: str = ""
    
    OAUTH_SECRET_KEY: str = ""  # For state parameter
```

### 3. Database Model Updates
```python
# backend/app/models/user.py - Add OAuth fields
class User(Base):
    # ... existing fields ...
    
    # OAuth fields
    oauth_provider = Column(String, nullable=True)  # 'google', 'github', etc.
    oauth_provider_id = Column(String, nullable=True, index=True)
    oauth_email = Column(String, nullable=True)
    oauth_name = Column(String, nullable=True)
    oauth_picture = Column(String, nullable=True)
    
    # Allow null password for OAuth users
    hashed_password = Column(String, nullable=True)
```

### 4. OAuth Service Implementation
```python
# backend/app/services/oauth_service.py
from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException
from sqlalchemy.orm import Session

class OAuthService:
    def __init__(self):
        self.oauth = OAuth()
        self._setup_providers()
    
    def _setup_providers(self):
        # Google OAuth
        self.oauth.register(
            name='google',
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={'scope': 'openid email profile'}
        )
        
        # GitHub OAuth
        self.oauth.register(
            name='github',
            client_id=settings.GITHUB_CLIENT_ID,
            client_secret=settings.GITHUB_CLIENT_SECRET,
            access_token_url='https://github.com/login/oauth/access_token',
            authorize_url='https://github.com/login/oauth/authorize',
            api_base_url='https://api.github.com/',
            client_kwargs={'scope': 'user:email'}
        )
    
    async def create_or_update_oauth_user(
        self, 
        provider: str, 
        user_info: dict, 
        db: Session
    ) -> User:
        # Check if user exists
        user = db.query(User).filter(
            User.oauth_provider == provider,
            User.oauth_provider_id == user_info['id']
        ).first()
        
        if not user:
            # Check if email already exists
            user = db.query(User).filter(
                User.email == user_info['email']
            ).first()
            
            if user and not user.oauth_provider:
                # Link existing account
                user.oauth_provider = provider
                user.oauth_provider_id = user_info['id']
            else:
                # Create new user
                user = User(
                    email=user_info['email'],
                    username=user_info['email'].split('@')[0],
                    oauth_provider=provider,
                    oauth_provider_id=user_info['id'],
                    oauth_name=user_info.get('name'),
                    oauth_picture=user_info.get('picture'),
                    is_active=True
                )
                db.add(user)
        
        db.commit()
        return user

oauth_service = OAuthService()
```

### 5. API Endpoints
```python
# backend/app/api/auth.py - Add OAuth endpoints
from fastapi import Request
from starlette.responses import RedirectResponse

@router.get("/auth/{provider}")
async def oauth_login(provider: str, request: Request):
    redirect_uri = request.url_for('oauth_callback', provider=provider)
    return await oauth_service.oauth.create_client(provider).authorize_redirect(
        request, redirect_uri
    )

@router.get("/auth/{provider}/callback")
async def oauth_callback(
    provider: str, 
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        token = await oauth_service.oauth.create_client(provider).authorize_access_token(request)
        
        # Get user info based on provider
        if provider == 'google':
            user_info = token['userinfo']
        elif provider == 'github':
            resp = await oauth_service.oauth.create_client('github').get('user', token=token)
            user_info = resp.json()
            # Get email separately for GitHub
            email_resp = await oauth_service.oauth.create_client('github').get('user/emails', token=token)
            emails = email_resp.json()
            user_info['email'] = next(e['email'] for e in emails if e['primary'])
        
        # Create or update user
        user = await oauth_service.create_or_update_oauth_user(provider, user_info, db)
        
        # Create JWT token
        access_token = create_access_token(data={"sub": user.email})
        
        # Redirect to frontend with token
        frontend_url = f"{settings.FRONTEND_URL}/oauth-success?token={access_token}"
        return RedirectResponse(url=frontend_url)
        
    except Exception as e:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error=oauth_failed"
        )
```

### 6. Frontend Implementation
```typescript
// frontend/src/pages/Auth/OAuthButtons.tsx
import { Google, GitHub, Microsoft } from '@mui/icons-material';

export const OAuthButtons: React.FC = () => {
  const handleOAuthLogin = (provider: string) => {
    window.location.href = `${API_URL}/auth/${provider}`;
  };
  
  return (
    <Box sx={{ mt: 2 }}>
      <Divider sx={{ my: 2 }}>Or continue with</Divider>
      
      <Stack spacing={1}>
        <Button
          fullWidth
          variant="outlined"
          startIcon={<Google />}
          onClick={() => handleOAuthLogin('google')}
        >
          Continue with Google
        </Button>
        
        <Button
          fullWidth
          variant="outlined"
          startIcon={<GitHub />}
          onClick={() => handleOAuthLogin('github')}
        >
          Continue with GitHub
        </Button>
        
        <Button
          fullWidth
          variant="outlined"
          startIcon={<Microsoft />}
          onClick={() => handleOAuthLogin('microsoft')}
        >
          Continue with Microsoft
        </Button>
      </Stack>
    </Box>
  );
};

// frontend/src/pages/Auth/OAuthCallback.tsx
export const OAuthCallback: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuthStore();
  
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');
    const error = params.get('error');
    
    if (token) {
      login(token);
      navigate('/dashboard');
    } else if (error) {
      navigate('/login?error=' + error);
    }
  }, []);
  
  return <LoadingSpinner message="Completing sign in..." />;
};
```

### 7. Account Settings Updates
```typescript
// Add to user settings page
<Box>
  <Typography variant="h6">Connected Accounts</Typography>
  {user.oauth_provider ? (
    <Chip
      icon={<Google />}
      label={`Connected with ${user.oauth_provider}`}
      color="primary"
    />
  ) : (
    <Typography>No connected accounts</Typography>
  )}
</Box>
```

## Environment Setup

### Google OAuth Setup
1. Go to https://console.cloud.google.com/
2. Create new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URIs:
   - http://localhost:8001/auth/google/callback (dev)
   - https://your-api-domain.com/auth/google/callback (prod)

### GitHub OAuth Setup
1. Go to https://github.com/settings/developers
2. Create new OAuth App
3. Set Authorization callback URL
4. Copy Client ID and Secret

## Security Considerations
- Use secure state parameter to prevent CSRF
- Validate redirect URIs
- Use HTTPS in production
- Store OAuth tokens securely
- Implement proper session management

## Success Criteria
- Users can sign up/login with Google
- Existing accounts can be linked
- OAuth users don't need passwords
- Multiple providers supported
- Smooth redirect flow
- Error handling for failed OAuth

## Dependencies
- authlib or python-social-auth
- Frontend routing for callbacks
- User model updates
- Environment variables for OAuth credentials

## Estimated Time: 3-4 days