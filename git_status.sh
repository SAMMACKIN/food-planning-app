#!/bin/bash
cd /Users/sammackin/Desktop/Claude\ Code\ Apps/Health\ App/food-planning-app
echo "Current directory: $(pwd)"
echo "Git branch: $(git branch --show-current)"
echo "Git status:"
git status --short
echo "Latest commit:"
git log --oneline -1