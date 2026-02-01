#!/bin/bash

# Backend changes
git add backend/main.py
git commit -m "Add auth and file listing endpoints"

git add backend/storage_service.py
git commit -m "Add file listing service function"

# Frontend config files
git add frontend/.gitignore
git commit -m "Add frontend gitignore"

git add frontend/package.json
git commit -m "Add frontend dependencies"

git add frontend/package-lock.json
git commit -m "Lock frontend dependency versions"

git add frontend/vite.config.js
git commit -m "Add Vite build configuration"

git add frontend/tailwind.config.js
git commit -m "Add Tailwind CSS configuration"

git add frontend/postcss.config.js
git commit -m "Add PostCSS configuration"

git add frontend/eslint.config.js
git commit -m "Add ESLint configuration"

git add frontend/index.html
git commit -m "Add frontend entry HTML"

git add frontend/README.md
git commit -m "Add frontend documentation"

# Frontend public assets
git add frontend/public/
git commit -m "Add public assets"

# Frontend source - Core
git add frontend/src/main.jsx
git commit -m "Add React entry point"

git add frontend/src/App.jsx
git commit -m "Add app routing logic"

git add frontend/src/App.css
git commit -m "Add app styles"

git add frontend/src/index.css
git commit -m "Add global styles and Tailwind imports"

# Frontend source - Services
git add frontend/src/services/api.js
git commit -m "Add API service layer"

# Frontend source - UI Components
git add frontend/src/components/ui/Button.jsx
git commit -m "Add Button component"

git add frontend/src/components/ui/Card.jsx
git commit -m "Add Card component"

git add frontend/src/components/ui/Input.jsx
git commit -m "Add Input component"

# Frontend source - Features
git add frontend/src/features/welcome/Welcome.jsx
git commit -m "Add Welcome landing page"

git add frontend/src/features/auth/Login.jsx
git commit -m "Add Login page with API integration"

git add frontend/src/features/files/Dashboard.jsx
git commit -m "Add Dashboard layout"

git add frontend/src/features/files/Upload.jsx
git commit -m "Add file upload component"

git add frontend/src/features/files/FileList.jsx
git commit -m "Add file list component"

echo "✅ All files committed successfully!"
