# Development Plan - Next Steps 🎯

**STATUS: CODE FREEZE** ✋

Current working state preserved in commit `83ae23a`. Test thoroughly before making changes.

---

## Immediate Priority (After Testing)

### 1. Clean Terminal Output ✨
**Problem:** Terminal is too verbose with timestamps and debug info

**Solution:**
- Replace all `log_step()` calls with silent execution
- Show only a clean progress bar/spinner
- Use `rich.progress.Progress` with nice bars
- Hide all technical details unless `--verbose` flag

**Changes needed:**
- `core/orchestrator.py`: Remove/hide all `log_step()` calls
- Add `--verbose` flag to CLI
- Use Rich's Progress for clean UI

---

### 2. Context Management for Large MRs 📦
**Problem:** Large MRs (>100 functions) may overwhelm LLM with too much context

**Current behavior:**
- Skips call graph if >100 functions ✅
- But still sends all 320 functions to LLM ❌

**Smart solution:**
```
IF changed_functions > 100:
    1. Prioritize functions with signature changes (BLOCKER)
    2. Group by file and summarize
    3. Send only:
       - All BLOCKER signature changes (full detail)
       - Top 50 most important other functions
       - Summary of remaining changes
    4. Multi-pass review:
       - Pass 1: Critical issues only
       - Pass 2: Code quality (optional)
```

**Implementation:**
- Add `skills/context_prioritizer.py`
- Modify `context_packager.py` to handle large MRs differently
- Add `--full` flag for complete analysis

---

### 3. Fix LLM Output Issues 🔧
**Problem:** LLM sometimes spams function titles instead of analysis

**Root cause:** Prompt might not be clear enough OR context is too large

**Solution:**
- Improve prompt in `review_generator.py`
- Add explicit instructions: "DO NOT list all functions, ONLY analyze issues"
- Limit context sent to LLM (see #2)
- Add output validation (if review is just titles, retry with better prompt)

---

## Implementation Order

**DO NOT implement until current state is tested!**

### Phase 1: Clean Output (30 min)
```bash
git checkout -b feature/clean-output

# Changes:
- Update orchestrator.py (hide logs)
- Add --verbose flag
- Use Rich Progress bars
- Test

git commit -m "Clean terminal output with progress bars"
```

### Phase 2: Context Management (2 hours)
```bash
git checkout -b feature/smart-context

# Changes:
- Add context_prioritizer.py
- Modify context_packager.py
- Add tests
- Test on large MR

git commit -m "Smart context prioritization for large MRs"
```

### Phase 3: Better Prompts (1 hour)
```bash
git checkout -b feature/better-prompts

# Changes:
- Improve prompt in review_generator.py
- Add output validation
- Test

git commit -m "Improved LLM prompts and output validation"
```

---

## Testing Protocol

Before ANY new commit becomes a "Working State":

1. **Test on 3 different MR sizes:**
   - Small (5-10 functions)
   - Medium (30-50 functions)
   - Large (100+ functions)

2. **Verify output quality:**
   - Check REVIEW.md is readable
   - Verify BLOCKER issues are found
   - No title spam
   - Proper formatting

3. **Performance check:**
   - Small: < 60s
   - Medium: < 90s
   - Large: < 150s

4. **If all pass:** Update UHOH.md with new working state

---

## Future Enhancements (After Stabilization)

### Optional Features
- [ ] Multi-pass review mode
- [ ] Summary mode (quick 30s review)
- [ ] Interactive chat after review
- [ ] MCP integration (Confluence/JIRA)
- [ ] Graphify integration (pre-built graph)
- [ ] Project planner skill
- [ ] Multiple language support

---

## Known Issues to Fix

1. **Ollama crashes on large context**
   - Current workaround: Use gemma2:9b
   - Better: Chunk context into smaller pieces

2. **Terminal too verbose**
   - Fix: Clean output (Phase 1)

3. **Title spam in output**
   - Fix: Better prompts (Phase 3)

4. **Large MR context overload**
   - Fix: Smart prioritization (Phase 2)

---

## Decision Log

| Decision | Date | Reason |
|----------|------|--------|
| Use Python (not TypeScript) | 2026-05-05 | tree-sitter faster, better AST |
| Only analyze changed functions | 2026-05-05 | 10x performance improvement |
| Skip call graph if >100 funcs | 2026-05-05 | grep is slow at scale |
| CODE FREEZE after Working State 1 | 2026-05-05 | Test before adding features |

---

**Remember:** Don't over-complicate! Keep it simple and working.

One feature at a time. Test thoroughly. Update UHOH.md.
