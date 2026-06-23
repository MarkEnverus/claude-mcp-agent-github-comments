# How to Remove Secrets from Git History

## What Happened in This Repo

1. **Commit with secret created**: Commit `168f4c5` had a GitHub token in `MCP_SERVER_SETUP_GUIDE.md`
2. **Push blocked**: GitHub's push protection detected the secret
3. **History rewritten**: Used `git reset --soft` to remove the problematic commit
4. **Clean commit created**: New commit `4beec06` without the secret
5. **Successfully pushed**: Clean history now on GitHub
6. **Local cleanup**: Deleted `docs` branch and ran garbage collection

## The Process Used (Step-by-Step)

### Step 1: Identify the Problem
```bash
# Push failed with error pointing to commit 168f4c5
git push origin main
# Error: "Push cannot contain secrets" in commit 168f4c5
```

### Step 2: Reset to Safe Point
```bash
# Reset HEAD to origin/main, keeping all changes staged
git reset --soft origin/main

# This removes the problematic commit(s) from history
# but keeps all your file changes staged and ready
```

### Step 3: Create New Clean Commit
```bash
# Create a new commit with all the good changes
git commit -m "Your clean commit message"
```

### Step 4: Push Successfully
```bash
git push origin main
# Success! The secret is no longer in the pushed history
```

### Step 5: Clean Up Locally
```bash
# Delete any branches with the secret
git branch -D docs

# Clean up orphaned commits
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

## Complete Guide: Remove Secrets from Git History

### Method 1: Recent Unpushed Commits (What We Used) ✅
**Use when:** Secret is in recent unpushed commits

```bash
# 1. Check how many commits ahead you are
git log --oneline origin/main..HEAD

# 2. Reset to last pushed commit (keeps changes staged)
git reset --soft origin/main

# 3. Review staged changes (ensure secret is gone)
git status
git diff --cached

# 4. Create new clean commit
git commit -m "Your clean commit message"

# 5. Push
git push origin main

# 6. Clean up locally
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

**Risk Level:** Low ⭐
**Pros:** Simple, safe, no force push needed
**Cons:** Only works for unpushed commits

### Method 2: Recently Pushed Commits
**Use when:** Secret was just pushed (within last few commits)

```bash
# 1. Find the commit BEFORE the one with the secret
git log --oneline

# 2. Interactive rebase to that commit
git rebase -i <commit-before-secret>^

# 3. In the editor, delete the line with the bad commit
#    Or mark it as 'drop' instead of 'pick'

# 4. Save and close the editor

# 5. Force push (WARNING: rewrites history!)
git push --force-with-lease origin main
```

**Risk Level:** Medium ⭐⭐
**Pros:** Can fix recently pushed commits
**Cons:** Requires force push, team coordination needed

### Method 3: Old Commits with BFG Repo-Cleaner
**Use when:** Secret appears in old commits across history

```bash
# Install
brew install bfg

# 1. Clone a fresh copy
git clone --mirror https://github.com/user/repo.git

# 2. Remove the secret
bfg --replace-text secrets.txt repo.git
# Where secrets.txt contains: YOUR_SECRET_HERE==>***REMOVED***

# 3. Clean up
cd repo.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 4. Force push
git push --force
```

**Risk Level:** High ⭐⭐⭐
**Pros:** Fast, handles multiple commits
**Cons:** Force push, everyone must re-clone

### Method 4: Using git-filter-repo (Most Powerful)
**Use when:** Complex cleanup needed across entire history

```bash
# Install
pip install git-filter-repo

# Remove file from all history
git filter-repo --path MCP_SERVER_SETUP_GUIDE.md --invert-paths

# Or remove specific text
git filter-repo --replace-text <(echo 'ghp_secrettoken==>***REMOVED***')

# Force push
git push --force
```

**Risk Level:** Very High ⭐⭐⭐⭐
**Pros:** Most powerful, handles complex scenarios
**Cons:** Rewrites entire history, advanced usage

## Quick Reference

| Scenario | Method | Command | Risk | Force Push? |
|----------|--------|---------|------|-------------|
| Unpushed commits | Reset soft | `git reset --soft origin/main` | Low | No ✅ |
| Just pushed | Interactive rebase | `git rebase -i` | Medium | Yes |
| Old commits | BFG | `bfg --replace-text` | High | Yes |
| Complex cleanup | git-filter-repo | `git filter-repo` | Very High | Yes |

## Prevention: Avoid Secrets in Git

### 1. Use .gitignore
```bash
# Add to .gitignore
.env
.env.local
*.pem
*.key
secrets.yaml
credentials.json
```

### 2. Use Environment Variables
```python
# ❌ Bad - Hardcoded secret
GITHUB_TOKEN = "ghp_xxxxx"

# ✅ Good - Environment variable
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
```

### 3. Use Git Secrets Tool
```bash
# Install
brew install git-secrets

# Set up in repo
cd your-repo
git secrets --install
git secrets --register-aws

# Scan history
git secrets --scan-history
```

### 4. Pre-commit Hooks
Create `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
```

Install:
```bash
pip install pre-commit
pre-commit install
```

### 5. GitHub Secret Scanning
Enable in repository settings:
- Settings → Security → Code security and analysis
- Enable "Secret scanning"
- Enable "Push protection"

## Important Warnings

### Before Force Pushing

⚠️ **Always backup first:**
```bash
git bundle create backup.bundle --all
```

⚠️ **Warn your team:**
- Notify all collaborators before rewriting history
- Choose a time when others aren't actively working
- Document the cleanup process

⚠️ **Coordinate with team:**
After force push, everyone needs to:
```bash
git fetch origin
git reset --hard origin/main
```

### After Rewriting History

1. **Revoke compromised secrets** immediately
   - GitHub tokens: https://github.com/settings/tokens
   - AWS keys: AWS Console → IAM
   - API keys: Your service provider

2. **Verify cleanup**
   ```bash
   # Search for the secret
   git log --all --source -S 'your-secret'
   ```

3. **Monitor for abuse**
   - Check GitHub audit log
   - Check AWS CloudTrail
   - Monitor API usage

## Testing Your Cleanup

```bash
# 1. Search for literal secret string
git log --all --source --full-history -S 'ghp_yourtoken'

# 2. Search in all commits for pattern
git rev-list --all | xargs git grep 'ghp_'

# 3. Check specific file's history
git log --all --full-history -- path/to/file

# 4. Verify branches
git branch -a

# 5. Check reflog
git reflog show --all
```

## Common Issues

### "Object not found" after cleanup
```bash
# Re-clone the repository
git clone https://github.com/user/repo.git
```

### Force push rejected
```bash
# Use --force-with-lease (safer than --force)
git push --force-with-lease origin main
```

### Secret still showing in old PR/issue comments
- GitHub's secret scanning may still detect it in comments
- Contact GitHub Support to purge from their caches
- Or manually edit/delete the comments

## Resources

- [GitHub: Removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)
- [git-filter-repo](https://github.com/newren/git-filter-repo)
- [Git Secrets](https://github.com/awslabs/git-secrets)
- [detect-secrets](https://github.com/Yelp/detect-secrets)

## Quick Command Summary

```bash
# For unpushed commits (safest)
git reset --soft origin/main
git commit -m "Clean commit"
git push origin main

# For pushed commits (requires force push)
git rebase -i HEAD~3  # Go back 3 commits
# Mark bad commit as 'drop'
git push --force-with-lease origin main

# Nuclear option (BFG)
bfg --delete-files secret.txt
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push --force

# Cleanup
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```
