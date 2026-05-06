# Known Issues - Working State 1

## Issue #1: LLM Output Repeats Function Names (Large MRs)

### Symptoms
- Review output lists all function names repeatedly
- No "Final Decision" section at the end
- Output says "APPROVED" or "COMMENTS_TO_ADDRESS" is missing
- Happens on large MRs (>100 changed functions)

### Root Cause
When there are many changed functions (e.g., 320 functions in AGS codebase):

1. **Context Packager** (`skills/context_packager.py`) sends ALL function details to LLM
2. **Massive Context** - Creates thousands of lines of function listings
3. **LLM Overwhelmed** - Ollama receives too much information
4. **Repetitive Output** - LLM just repeats function names instead of analyzing
5. **Truncation** - Output may be cut off before "Final Decision"

### Example
```
AGS repo test:
- 140 files changed
- 320 functions modified
- Context sent: ~15,000 lines
- LLM output: Lists all 320 function names, no analysis
```

### Current Workaround
For large MRs, the tool automatically **skips call graph** (>100 functions) to save time, but still sends all function details to LLM.

This helps with performance but doesn't fix the output quality issue.

### Why Not Fixed Yet?
**Intentionally deferred** - Working State 1 is marked as stable for testing. The fix requires significant changes (see PLAN.md Phase 2: Smart Context Management).

### Planned Fix (Phase 2)
See PLAN.md for details:

```
IF changed_functions > 100:
    1. Prioritize functions with signature changes (BLOCKER)
    2. Group by file and summarize
    3. Send only:
       - All BLOCKER signature changes (full detail)
       - Top 50 most important functions
       - Summary of remaining changes
    4. Multi-pass review option
```

### When This Issue Occurs
- ✅ **Works fine:** Small/medium MRs (5-50 functions)
- ⚠️ **Degraded:** Large MRs (50-100 functions) - slow but works
- ❌ **Affected:** Huge MRs (>100 functions) - output quality issues

### Temporary Solution for Users
If you hit this issue:

1. **Break up the MR** into smaller branches
2. **Use faster model** to reduce token generation:
   ```bash
   mr-review --model gemma2:9b
   ```
3. **Focus on critical files** - Review subset manually
4. **Wait for Phase 2 fix** (smart context prioritization)

---

## Issue #2: Verbose Terminal Output

### Symptoms
- Too many log messages during review
- Timestamps and debug info clutter output
- Hard to see progress

### Status
**Documented** in PLAN.md Phase 1 (Clean Output)

### Planned Fix
- Use Rich Progress bars only
- Hide technical logs unless `--verbose` flag
- Clean, minimal output by default

---

## Issue #3: Ollama Crashes on Large Context

### Symptoms
- Ollama crashes with `GGML_ASSERT` error
- Happens on very large MRs or complex codebases

### Root Cause
Related to Issue #1 - too much context sent to Ollama

### Workaround
```bash
# Restart Ollama
pkill ollama
ollama serve &

# Use smaller model
mr-review --model gemma2:9b
```

---

## Testing Status

### ✅ Tested & Working
- Small MRs (5-20 functions): Perfect output, 30-60 seconds
- Medium MRs (20-50 functions): Good output, 60-90 seconds
- Signature change detection: Works great (25 BLOCKERS found)
- Duplicate detection: Works correctly

### ⚠️ Known Limitations
- Large MRs (>100 functions): Output quality degrades
- Very large MRs (>200 functions): High chance of repetitive output

---

## Summary

**Working State 1 is STABLE and WORKING** for typical use cases (small-medium MRs).

The large MR issue is **documented and understood**, with a clear fix planned in Phase 2.

**Recommendation:** Use current version for normal workflows. Don't implement Phase 2 fixes until more testing is done on small/medium MRs.

---

Last Updated: 2026-05-06
Current State: Working State 1 (commit 83ae23a)
