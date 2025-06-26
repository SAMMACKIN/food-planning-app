#!/bin/bash

# Detect which branch we're on and set environment variables accordingly
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
echo "🌿 Building for branch: $BRANCH"

if [ "$BRANCH" = "preview" ]; then
    echo "🔧 Setting preview environment variables"
    export REACT_APP_API_URL="https://food-planning-app-preview.up.railway.app"
    export REACT_APP_VERSION="1.0.0-preview"
    export REACT_APP_ENVIRONMENT="preview"
    
    # Create temporary .env.local for this build
    cat > .env.local << EOF
REACT_APP_API_URL=https://food-planning-app-preview.up.railway.app
REACT_APP_VERSION=1.0.0-preview
REACT_APP_ENVIRONMENT=preview
EOF
    
elif [ "$BRANCH" = "master" ] || [ "$BRANCH" = "main" ]; then
    echo "🔧 Setting production environment variables"
    export REACT_APP_API_URL="https://food-planning-app-production.up.railway.app"
    export REACT_APP_VERSION="1.0.0"
    export REACT_APP_ENVIRONMENT="production"
    
    # Create temporary .env.local for this build
    cat > .env.local << EOF
REACT_APP_API_URL=https://food-planning-app-production.up.railway.app
REACT_APP_VERSION=1.0.0
REACT_APP_ENVIRONMENT=production
EOF
    
else
    echo "🔧 Setting development environment variables"
    export REACT_APP_API_URL="http://localhost:8001"
    export REACT_APP_VERSION="1.0.0-dev"
    export REACT_APP_ENVIRONMENT="development"
    
    # Create temporary .env.local for this build
    cat > .env.local << EOF
REACT_APP_API_URL=http://localhost:8001
REACT_APP_VERSION=1.0.0-dev
REACT_APP_ENVIRONMENT=development
EOF
fi

echo "🔗 API URL: $REACT_APP_API_URL"
echo "📦 Version: $REACT_APP_VERSION"
echo "🌍 Environment: $REACT_APP_ENVIRONMENT"

# Build the app
echo "🚀 Starting build..."
npm run build

# Clean up temporary env file
rm -f .env.local

echo "✅ Build complete!"