# Preview Environment Workflow

## 🎯 Purpose
Test new features safely before deploying to production.

## 🌍 Environment URLs

### Production (Live App)
- **Frontend**: https://food-planning-app.vercel.app
- **Backend**: https://food-planning-app-production.up.railway.app

### Preview (Testing)
- **Frontend**: https://food-planning-app-git-preview-sams-projects-c6bbe2f2.vercel.app
- **Backend**: Create separate Railway service for preview

## 🔄 Workflow Steps

### 1. Development Process
```bash
# Switch to preview branch
git checkout preview

# Make changes to code
# Test locally if possible

# Commit changes
git add .
git commit -m "Feature: description"
git push origin preview
```

### 2. Automatic Deployments
- **Vercel**: Automatically deploys `preview` branch to preview URL
- **Railway**: Deploy manually to preview service (separate from production)

### 3. Testing Process
1. **Visit preview URLs** to test new features
2. **Verify functionality** works as expected
3. **Check for errors** in browser console
4. **Test on mobile/desktop** responsiveness

### 4. Production Deployment
```bash
# If preview tests pass:
git checkout master
git merge preview
git push origin master

# If preview tests fail:
# Fix issues on preview branch and repeat testing
```

## 🛡️ Safety Benefits
- ✅ **No production downtime** from broken features
- ✅ **Test with real production data** (but separate database)
- ✅ **Catch errors early** before users see them
- ✅ **Multiple people can test** preview links

## 🚀 Quick Commands

```bash
# Start new feature
git checkout preview
git pull origin master  # Get latest changes

# Deploy to preview
git add . && git commit -m "Feature: name" && git push origin preview

# Deploy to production (after testing)
git checkout master && git merge preview && git push origin master
```