# Quick Start - MR Review Agent

## Installation (One Time)

```bash
cd /Users/raghavkumarr/Desktop/AGS/mr-review-v3
./install.sh
```

This will:
- ✅ Install to `~/.mr-review-agent`
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Create global `mr-review` command

## Add to PATH (One Time)

Add this line to your `~/.zshrc`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Then:
```bash
source ~/.zshrc
```

## Usage (From Any Repo)

### 1. Navigate to Your Repo

```bash
cd /Users/raghavkumarr/Desktop/AGS/artwork-generation-service-node
```

### 2. Checkout Your Branch

```bash
# Check current branch
git branch

# Checkout your feature branch
git checkout your-branch-name
```

### 3. Run Review

```bash
# Simple - review current branch vs main
mr-review

# Specify base branch
mr-review --base develop

# Custom output location
mr-review --output ./my-review.md
```

### 4. Check Output

```bash
cat REVIEW.md
```

## Example on AGS Repo

```bash
# Go to AGS repo
cd /Users/raghavkumarr/Desktop/AGS/artwork-generation-service-node

# See available branches
git branch

# Checkout a branch
git checkout chore/AG-5120-refactor-image-transfere-file-compose

# Run review
mr-review

# Should complete in 60-120 seconds
# Output: REVIEW.md in current directory
```

## Testing

```bash
# Test Ollama connection
mr-review test-ollama

# Should show: ✓ Ollama is working!
```

## Performance Expectations

**NEW: Smart Function Extraction**
- Only analyzes functions that actually changed
- Ignores unchanged functions in modified files
- 10x faster on large MRs

| Branch Size | Files | Changed Functions | Expected Time |
|-------------|-------|-------------------|---------------|
| Small       | 2-5   | 5-10             | 30-60s        |
| Medium      | 6-15  | 10-30            | 60-90s        |
| Large       | 16-50 | 30-100           | 90-120s       |
| Huge        | 50+   | 100+             | Skip graph    |

## What It Analyzes

✅ **Functions that changed** (not entire files)
✅ **Signature changes** (BLOCKER if params added/removed)
✅ **Duplicate interfaces**
✅ **Code quality** (unnecessary comments, deep nesting)
✅ **Better implementations**

## Troubleshooting

### "mr-review: command not found"

```bash
# Make sure ~/.local/bin is in PATH
echo $PATH | grep ".local/bin"

# If not, add to ~/.zshrc
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Review Takes Too Long

```bash
# Check how many files changed
git diff main --stat | tail -1

# If > 50 files, it will skip call graph automatically
# Should still complete in 2-3 minutes
```

### "Not a git repository"

```bash
# Make sure you're in a git repo
ls -la .git

# Make sure you're not on main
git branch
```

## Advanced Options

```bash
# Use different model
mr-review --model gemma2:9b  # Faster but less accurate

# Different base branch
mr-review --base develop

# Save to specific location
mr-review --output /tmp/review.md

# Show all options
mr-review --help
```

## Uninstall

```bash
rm -rf ~/.mr-review-agent
rm ~/.local/bin/mr-review
```

---

**Ready to test!** 🚀

Run it on your AGS repo:
```bash
cd /Users/raghavkumarr/Desktop/AGS/artwork-generation-service-node
mr-review
```
