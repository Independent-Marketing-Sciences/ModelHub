# GitHub Token Setup for Publishing Releases

## Why You Need a Token

Even though your repository is **public**, you need a GitHub Personal Access Token (PAT) to:
- Automatically publish releases
- Upload release assets (installer files)
- Update the `latest.yml` file for auto-updates

**Note:** The old token in package.json was invalidated and has been removed.

## Creating a New GitHub Token

### Step 1: Generate Token on GitHub

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a name: `ModelHub Releases`
4. Set expiration: `No expiration` (or your preference)
5. Select scopes:
   - ✅ **`repo`** (Full control of private repositories)
     - This includes: `repo:status`, `repo_deployment`, `public_repo`, `repo:invite`, `security_events`

6. Click "Generate token"
7. **IMPORTANT:** Copy the token immediately (it won't be shown again!)
   - Format: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### Step 2: Set Token as Environment Variable

**Option A: Set Temporarily (For Current Session)**

```bash
# Windows CMD
set GH_TOKEN=ghp_your_new_token_here

# Then run:
npm run electron:publish:win
```

**Option B: Set Permanently (Recommended)**

1. Open Windows Start Menu
2. Search for "Environment Variables"
3. Click "Edit the system environment variables"
4. Click "Environment Variables..." button
5. Under "User variables", click "New..."
6. Variable name: `GH_TOKEN`
7. Variable value: `ghp_your_new_token_here`
8. Click OK on all dialogs
9. **Restart your terminal/VS Code**

**Option C: Use .env file (For Development)**

1. Create `.env` file in project root:
```
GH_TOKEN=ghp_your_new_token_here
```

2. Update package.json script:
```json
"electron:publish:win": "dotenv -e .env -- electron-builder --win --config electron-builder.yml --publish always"
```

3. Install dotenv-cli:
```bash
npm install --save-dev dotenv-cli
```

**⚠️ NEVER commit .env to git!** (Already in .gitignore)

### Step 3: Test the Token

```bash
# Set the token (if using temporary method)
set GH_TOKEN=ghp_your_new_token_here

# Test publishing
npm run electron:publish:win
```

## Publishing Releases

### Method 1: Automatic Publish (With Token)

```bash
# Make sure GH_TOKEN is set
npm run electron:publish:win
```

This will:
1. Build the installer
2. Create GitHub release with version from package.json
3. Upload installer and latest.yml
4. Make release public

### Method 2: Manual Publish (Without Token)

```bash
# Build locally
npm run electron:build:win

# Then manually:
# 1. Go to GitHub > Releases > New Release
# 2. Tag: v1.0.3
# 3. Upload files from dist/:
#    - Modelling Mate Setup 1.0.3.exe
#    - latest.yml
# 4. Publish
```

## Security Best Practices

### ✅ DO:
- Store token in environment variable
- Use token with minimum required scopes (`repo` only)
- Regenerate token if exposed
- Set expiration date (optional but recommended)

### ❌ DON'T:
- Put token in package.json (removed ✅)
- Commit token to git
- Share token in chat/email
- Use token in CI/CD without secrets management

## Troubleshooting

### Error: "Bad credentials" (401)

**Cause:** Token is invalid or expired

**Solution:**
1. Generate a new token (steps above)
2. Update environment variable
3. Restart terminal
4. Try again

### Error: "Resource not accessible by integration" (403)

**Cause:** Token doesn't have `repo` scope

**Solution:**
1. Go to token settings: https://github.com/settings/tokens
2. Click on your token
3. Ensure `repo` is checked
4. If not, create a new token with proper scopes

### Error: "Not Found" (404)

**Cause:** Repository name or owner is wrong

**Solution:**
Check `electron-builder.yml`:
```yaml
publish:
  provider: github
  owner: Independent-Marketing-Sciences
  repo: ModelHub
```

### Error: Release already exists

**Cause:** Version tag already exists on GitHub

**Solution:**
1. Increment version in package.json
2. OR delete existing release/tag on GitHub
3. Try again

## Current Setup

Your repository configuration:
- **Owner:** Independent-Marketing-Sciences
- **Repo:** ModelHub
- **Visibility:** Public ✅
- **Publish:** GitHub Releases
- **Token:** None (needs to be set)

## Quick Reference

```bash
# Check if token is set
echo %GH_TOKEN%

# Set token (temporary)
set GH_TOKEN=ghp_your_token_here

# Build only (no publish)
npm run electron:build:win

# Build and publish (needs token)
npm run electron:publish:win

# Check releases on GitHub
start https://github.com/Independent-Marketing-Sciences/ModelHub/releases
```

## Alternative: GitHub CLI (gh)

If you have GitHub CLI installed:

```bash
# Login with gh
gh auth login

# Publish release manually
gh release create v1.0.3 "dist/Modelling Mate Setup 1.0.3.exe" "dist/latest.yml" --title "Version 1.0.3" --notes "Release notes here"
```

## For Team Members

Share this guide with team members who need to publish releases. Each person should:
1. Create their own GitHub token
2. Set it in their local environment
3. Never share their token

---

**Next Steps:**
1. ✅ Generate new GitHub token
2. ✅ Set as environment variable
3. ✅ Test with: `npm run electron:publish:win`
4. ✅ Verify release appears on GitHub
