# 🚀 Deploy Your Food Planning App - Step by Step

## Step 1: Push to GitHub (YOU DO THIS)

```bash
cd "/Users/sammackin/Desktop/Claude Code Apps/Health App/food-planning-app"
git remote add origin https://github.com/SAMMACKIN/food-planning-app.git
git push -u origin master
```

## Step 2: Deploy Backend to Railway

1. **Go to**: https://railway.app
2. **Sign in** with your GitHub account
3. **Click**: "Deploy from GitHub repo"
4. **Select**: `SAMMACKIN/food-planning-app`
5. **IMPORTANT**: Set **Root Directory** to `backend`
6. **Click Deploy**
7. **Copy the deployment URL** (something like: `https://backend-production-xxxx.up.railway.app`)

## Step 3: Deploy Frontend to Vercel

1. **Go to**: https://vercel.com
2. **Sign in** with your GitHub account  
3. **Click**: "New Project"
4. **Import**: `SAMMACKIN/food-planning-app`
5. **IMPORTANT**: Set **Root Directory** to `frontend`
6. **Add Environment Variable**:
   - Name: `REACT_APP_API_URL`
   - Value: `[YOUR_RAILWAY_URL]/api/v1` (replace with your Railway URL from Step 2)
7. **Click Deploy**

## Step 4: Update CORS (AFTER DEPLOYMENT)

After you get your Vercel URL, update the backend CORS:

1. Edit `backend/simple_app.py`
2. Replace the CORS section with your actual URLs:
```python
allow_origins=[
    "http://localhost:3000",
    "https://your-actual-vercel-url.vercel.app",  # YOUR REAL URL
    "https://*.vercel.app"
]
```
3. Commit and push the change
4. Railway will auto-redeploy

## Final Result

- **Backend API**: `https://your-railway-url.up.railway.app`
- **Frontend App**: `https://your-vercel-url.vercel.app`
- **Total Cost**: ~$5/month

## ✅ Your app is ready for production!

The app includes:
- User authentication
- Family member management  
- Pantry management with 20 pre-loaded ingredients
- Responsive Material-UI design
- Production-ready database

Need help? The deployment files are all ready - just follow the steps above!