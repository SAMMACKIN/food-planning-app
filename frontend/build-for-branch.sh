#!/bin/bash

# Detect environment from Vercel or git branch
if [ ! -z "$VERCEL_GIT_COMMIT_REF" ]; then
    BRANCH="$VERCEL_GIT_COMMIT_REF"
    echo "🌿 Building for Vercel branch: $BRANCH"
elif [ ! -z "$VERCEL_ENV" ]; then
    if [ "$VERCEL_ENV" = "preview" ]; then
        BRANCH="preview"
    elif [ "$VERCEL_ENV" = "production" ]; then
        BRANCH="master"
    else
        BRANCH="development"
    fi
    echo "🌿 Building for Vercel environment: $VERCEL_ENV (branch: $BRANCH)"
else
    BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
    echo "🌿 Building for local branch: $BRANCH"
fi

if [ "$BRANCH" = "preview" ]; then
    echo "🔧 Setting preview environment variables"
    export REACT_APP_API_URL="https://food-planning-app-preview.up.railway.app"
    export REACT_APP_VERSION="1.0.0-preview"
    export REACT_APP_ENVIRONMENT="preview"
    
elif [ "$BRANCH" = "master" ] || [ "$BRANCH" = "main" ]; then
    echo "🔧 Setting production environment variables"
    export REACT_APP_API_URL="https://food-planning-app-production.up.railway.app"
    export REACT_APP_VERSION="1.0.0"
    export REACT_APP_ENVIRONMENT="production"
    
else
    echo "🔧 Setting development environment variables"
    export REACT_APP_API_URL="http://localhost:8001"
    export REACT_APP_VERSION="1.0.0-dev"
    export REACT_APP_ENVIRONMENT="development"
fi

echo "🔗 API URL: $REACT_APP_API_URL"
echo "📦 Version: $REACT_APP_VERSION"
echo "🌍 Environment: $REACT_APP_ENVIRONMENT"

# Build the app
echo "🚀 Starting build..."
npm run build

echo "✅ Build complete!"