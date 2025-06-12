# Deployment Guide

## Quick Deploy to Production

### 1. Push to GitHub
```bash
# If you haven't already:
git remote add origin https://github.com/YOUR_USERNAME/food-planning-app.git
git push -u origin master
```

### 2. Deploy Backend to Railway

1. Go to [railway.app](https://railway.app) and sign in with GitHub
2. Click "Deploy from GitHub repo"
3. Select your `food-planning-app` repository
4. Choose the **backend** folder for deployment
5. Railway will auto-detect the Python app and deploy it
6. Your backend will be available at: `https://your-app-name.up.railway.app`

### 3. Deploy Frontend to Vercel

1. Go to [vercel.com](https://vercel.com) and sign in with GitHub
2. Click "New Project" and select your `food-planning-app` repository
3. Set the **Root Directory** to `frontend`
4. Add environment variable:
   - Key: `REACT_APP_API_URL`
   - Value: `https://your-railway-backend-url.up.railway.app/api/v1`
5. Deploy! Your frontend will be available at: `https://your-app.vercel.app`

### 4. Update CORS Settings

After deployment, update the backend CORS settings in `backend/simple_app.py`:
```python
allow_origins=[
    "http://localhost:3000",
    "https://your-app.vercel.app",  # Add your actual Vercel URL
    "https://*.vercel.app"
]
```

## Environment Variables

### Backend (Railway)
- `PORT` - Automatically set by Railway
- `DATABASE_URL` - Optional for production database

### Frontend (Vercel)
- `REACT_APP_API_URL` - Your Railway backend URL + `/api/v1`

## Cost Estimate
- **Railway**: $5/month for backend
- **Vercel**: Free tier (sufficient for most use cases)
- **Total**: ~$5/month

## Domain Setup (Optional)
1. Purchase domain from any registrar
2. In Vercel: Settings → Domains → Add custom domain
3. Update DNS records as instructed
4. SSL certificate automatically provisioned