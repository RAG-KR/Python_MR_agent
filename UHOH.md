# UHOH - Working State Tracker 🚨

This file tracks all tested, working commits so you can easily revert to a stable state.

---

## Working State 1 ✅ (Current)

**Commit:** `83ae23a`
**Date:** 2026-05-05
**Status:** TESTED & WORKING

### Features
- ✅ Smart function extraction (only changed functions analyzed)
- ✅ Fast preprocessing: 30-40 seconds for 140 files
- ✅ Signature change detection (BLOCKER priority)
- ✅ Duplicate interface detection
- ✅ Skips call graph for large MRs (>100 functions)
- ✅ Uses local Ollama (gemma4:26b)

### Performance
- **Tested on:** AGS codebase (140 files, 320 changed functions)
- **Found:** 25 BLOCKER signature changes
- **Time:** ~2 minutes total

### Known Issues
- ⚠️ Ollama can crash on very large contexts (use gemma2:9b as fallback)
- ⚠️ Terminal output is verbose (needs cleanup)
- ⚠️ Large MRs may spam titles in MD output

### How to Revert to This State
```bash
cd /Users/raghavkumarr/Desktop/AGS/mr-review-v3
git checkout 83ae23a
source .venv/bin/activate
```

### How to Use
```bash
cd /path/to/your/typescript/repo
git checkout your-branch
mr-review --base main
```

---

## Future States

### Working State 2 (Planned)
- [ ] Clean terminal output (nice loader only)
- [ ] Better context management for large MRs
- [ ] Improved error handling

### Working State 3 (Planned)
- [ ] Smarter LLM prompt to avoid title spam
- [ ] Multi-pass review for huge MRs
- [ ] Summary mode for quick reviews

---

## Emergency Rollback

If something breaks, quickly revert to last working state:

```bash
cd /Users/raghavkumarr/Desktop/AGS/mr-review-v3

# See all commits
git log --oneline

# Revert to Working State 1
git checkout 83ae23a

# Or create a branch from it
git checkout -b fallback-state-1 83ae23a

# Reinstall if needed
./install.sh
source ~/.zshrc
```

---

## Testing Checklist

Before marking a state as "WORKING", test:

- [ ] Small MR (5-10 functions): < 60 seconds
- [ ] Medium MR (10-50 functions): < 90 seconds
- [ ] Large MR (50-100 functions): < 120 seconds
- [ ] Finds BLOCKER signature changes
- [ ] Generates readable REVIEW.md
- [ ] No crashes or hangs
- [ ] Ollama works without errors

---

## Version History

| State | Commit | Date | Status | Notes |
|-------|--------|------|--------|-------|
| 1 | 83ae23a | 2026-05-05 | ✅ WORKING | Initial smart function extraction |
| 2 | TBD | TBD | 🚧 PLANNED | Clean output + context management |
| 3 | TBD | TBD | 🚧 PLANNED | Large MR optimization |

---

**Last Updated:** 2026-05-05
**Current Working State:** State 1 (83ae23a)
