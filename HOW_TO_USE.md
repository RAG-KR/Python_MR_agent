# How to Use MR Review Agent

## Quick Setup (One Time)

### 1. Create the `mr-review` Alias

Add this to your `~/.zshrc` (or `~/.bashrc` if using bash):

```bash
# MR Review Agent
alias mr-review='function _mr_review() {
  AGENT_DIR="/Users/raghavkumarr/Desktop/AGS/mr-review-v3"
  cd "$AGENT_DIR" && source .venv/bin/activate && python cli.py review "$@";
}; _mr_review'
```

Then reload your shell:
```bash
source ~/.zshrc
```

### 2. Test It Works

```bash
mr-review --help
```

---

## Usage

### Basic Usage

```bash
# 1. Go to your TypeScript repo
cd /Users/raghavkumarr/Desktop/AGS/artwork-generation-service-node

# 2. See available branches
git branch

# 3. Checkout the branch you want to review
git checkout feature/your-branch-name

# 4. Run review
mr-review --base main

# 5. Check output
cat REVIEW.md
```

### Options

```bash
# Review against different base branch
mr-review --base develop

# Use different model (faster but less accurate)
mr-review --base main --model gemma2:9b

# Custom output location
mr-review --base main --output /tmp/my-review.md

# Specify repo path (if not in repo directory)
mr-review --repo /path/to/repo --base main
```

---

## What It Does

**Smart Function Extraction:**
- Only analyzes functions that actually changed
- Ignores unchanged code in modified files
- Fast: 30-40 seconds for preprocessing

**What It Detects:**
- ✅ Signature changes (BLOCKER priority)
- ✅ Parameter additions/removals
- ✅ Type changes
- ✅ Duplicate interfaces
- ✅ Code quality issues

**Performance:**
- Small MR (5-10 changed functions): 30-60 seconds
- Medium MR (10-50 changed functions): 60-90 seconds
- Large MR (50-100 changed functions): 90-120 seconds
- Huge MR (>100 changed functions): Skips call graph, 2-3 minutes

---

## Example Workflow

```bash
# AGS repo example
cd /Users/raghavkumarr/Desktop/AGS/artwork-generation-service-node

# List branches
git branch -a

# Checkout a branch
git checkout feature/AG-5099-productionize-changes-for-resize

# Run review
mr-review --base main

# Output saved to: REVIEW.md
```

---

## Troubleshooting

### "mr-review: command not found"

Make sure you added the alias to `~/.zshrc` and ran:
```bash
source ~/.zshrc
```

### "Not a git repository"

You must be inside a git repository:
```bash
cd /path/to/your/repo
git status  # Should show git info
```

### Ollama Crashes

If you see `GGML_ASSERT` errors:
```bash
# Restart Ollama
pkill ollama
ollama serve &
sleep 5

# Try again
mr-review --base main
```

Or use a smaller model:
```bash
mr-review --base main --model gemma2:9b
```

### Review Takes Too Long

Check how many files changed:
```bash
git diff main --stat | tail -1
```

If >50 files, the agent automatically skips call graph building (for performance).

---

## Advanced

### Test Ollama Connection

```bash
# From anywhere
cd /Users/raghavkumarr/Desktop/AGS/mr-review-v3
source .venv/bin/activate
python cli.py test-ollama
```

### Run Without Alias

```bash
cd /Users/raghavkumarr/Desktop/AGS/your-repo
source /Users/raghavkumarr/Desktop/AGS/mr-review-v3/.venv/bin/activate
python /Users/raghavkumarr/Desktop/AGS/mr-review-v3/cli.py review --base main
```

---

## What Gets Committed

**Current Working State:**
- ✅ Smart function extraction (only changed functions)
- ✅ Signature change detection (BLOCKER priority)
- ✅ Duplicate interface detection
- ✅ Fast preprocessing (30-40s)
- ✅ Local Ollama integration
- ✅ Auto-skips call graph for large MRs

**Tested Successfully:**
- AGS codebase: 140 files → 320 changed functions
- 25 BLOCKER signature changes detected
- Total time: ~2 minutes

---

**That's it!** Now you can run `mr-review` from any TypeScript repo. 🚀
