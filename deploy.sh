#!/bin/bash

# Deployment script for Workforce Backend
# This script helps you deploy the fixed version to Render

echo "=========================================="
echo "Workforce Backend - Deployment Helper"
echo "=========================================="
echo ""

# Check if git is clean
if [[ -n $(git status -s) ]]; then
    echo "📝 You have uncommitted changes."
    echo ""
    echo "Files changed:"
    git status -s
    echo ""
    read -p "Do you want to commit these changes? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "📦 Staging all changes..."
        git add .
        
        echo ""
        echo "💬 Committing with deployment fix message..."
        git commit -m "Fix database schema and auth responses for deployment

- Added migration for verification_token and token_expires_at columns
- Enhanced migrate.py with auto-patching for schema
- Updated auth endpoints to return user data for frontend routing
- Created render.yaml for proper deployment configuration
- Added verification and testing scripts"
        
        echo ""
        echo "✅ Changes committed!"
    else
        echo ""
        echo "⚠️  Skipping commit. Please commit manually before deploying."
        exit 1
    fi
else
    echo "✅ Git working directory is clean."
fi

echo ""
echo "🚀 Pushing to remote repository..."
git push origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ DEPLOYMENT INITIATED"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "1. Go to your Render dashboard"
    echo "2. Watch the deployment logs"
    echo "3. Wait for deployment to complete"
    echo ""
    echo "Test your deployment with:"
    echo "curl -X POST https://workforce-backend-kfxw.onrender.com/api/auth/register/client \\"
    echo "  -H 'Content-Type: application/json' \\"
    echo "  -d '{\"email\":\"test@example.com\",\"password\":\"pass123\",\"company_name\":\"Test\"}'"
    echo ""
    echo "Expected: 201 response with access_token, refresh_token, and user data"
    echo ""
    echo "📚 For more details, see:"
    echo "   - QUICK_DEPLOY_GUIDE.md"
    echo "   - DEPLOYMENT_FIX.md"
    echo "=========================================="
else
    echo ""
    echo "❌ Push failed. Please check your git configuration and try again."
    exit 1
fi

