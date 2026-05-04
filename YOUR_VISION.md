# Your Vision for MR Review Agent

## The Core Problem
Current implementation is too slow (15+ minutes) because something is broken - either the call graph is hanging, or the LLM prompt is causing issues.

## Your Key Insights

### 1. Pre-Processing is Key
**ALL context gathering must happen BEFORE the LLM even starts.**

```
PRE-PROCESSING:
✓ Parse git diff
✓ Extract changed functions
✓ Check if function SIGNATURE changed (params, return type)
✓ Build call graph → who calls these functions
✓ Find duplicate code
✓ Find similar patterns
✓ Package everything

LLM JOB:
✓ READ the pre-computed context
✓ Validate contract matches
✓ Check DRY principle
✓ Find code quality issues
✓ Format structured output
```

### 2. Function Signature Changes are Critical
**This is the most important thing to catch:**

```typescript
// Before
function processPayment(userId: string, amount: number) { ... }

// After (signature changed!)
function processPayment(userId: string, amount: number, currency: string) { ... }

// But caller wasn't updated:
orderService.processPayment(userId, amount); // ❌ Missing currency!
```

**The agent MUST:**
1. Detect this signature change in git diff
2. Find all callers of `processPayment`
3. Check if they match the new signature
4. Flag mismatches as BLOCKER

### 3. Use Abstract Syntax Tree (AST)
**For fast, accurate parsing:**

Options:
- TypeScript Compiler API (for TS/JS files)
- Python `ast` module (if using Python)
- tree-sitter (multi-language)

**What to extract:**
- Function name
- Parameters (name, type, optional?)
- Return type
- Location (file:line)

### 4. Call Graph Building
**Build a hashmap/dependency graph:**

```javascript
{
  "processPayment": [
    { file: "order.service.ts", line: 123 },
    { file: "subscription.service.ts", line: 45 },
    { file: "refund.service.ts", line: 67 }
  ],
  "validateCard": [
    { file: "payment.service.ts", line: 89 }
  ]
}
```

**Fast lookup:**
- Use hashmap with chaining
- Index functions by name
- Store all call sites

### 5. The LLM Should NOT Search
**WRONG approach:**
```
Prompt: "Find all places where processPayment is called and check if they match"
```
❌ LLM tries to manually search → 15 minutes → hangs

**RIGHT approach:**
```
Prompt:
## Function Signature Changes

### processPayment() signature changed
**New:** processPayment(userId, amount, currency)
**Called by:**
- order.service.ts:123
- subscription.service.ts:45
- refund.service.ts:67

ACTION: Verify each caller uses 3 parameters.
```
✅ LLM just reads → 60 seconds → works

### 6. Structured Output Format
**Exact format you want:**

```markdown
# Code Review Report

## What This MR Does
[3-5 sentences explaining the changes]

## Current Issues

### BLOCKER (must fix):
**[Issue Title]** in file.ts:line
❌ Current (problematic code)
✅ Fix (corrected code)
**Impact:** Why this is critical

### SHOULD FIX:
- Issue with file:line reference

## Future Concerns
[Scalability, technical debt, risks]

## Code Quality
[DRY violations, clean code observations]

## What Was Done Well
[Positive feedback]

## Comments Summary
- Must fix: # items
- Should fix: # items

## Final Decision
**Status:** APPROVED / COMMENTS TO ADDRESS
**Files:** N | **Risk:** LOW/MEDIUM/HIGH
**Reason:** One sentence why
```

### 7. What to Check (LLM's Job)

**Contract Mismatches (BLOCKER priority):**
- Function signature changes without updating callers
- Interface mismatches
- Type mismatches
- Missing required properties

**Code Quality:**
- DRY violations (duplicate code)
- Unnecessary comments
- Complex logic that should be simplified
- Poor variable naming

**Clean Code Principles:**
- Single Responsibility Principle
- Functions too long (>50 lines)
- Deep nesting (>3 levels)
- Magic numbers
- Commented-out code

**Security:**
- SQL injection
- XSS vulnerabilities
- Hardcoded secrets
- SSRF risks

### 8. Performance Requirements
**Must complete in:**
- Small MR (2-5 files): 30-60 seconds
- Medium MR (6-15 files): 60-90 seconds
- Large MR (16-30 files): 90-120 seconds

**If slower than this, something is broken.**

### 9. Tools to Use

**For parsing:**
- TypeScript Compiler API (fastest for TS/JS)
- Python `ast` module (if using Python)
- tree-sitter (multi-language support)

**For searching:**
- `grep` or `ripgrep` (find function calls fast)
- RegEx patterns for function invocations
- AST traversal for accuracy

**For graph building:**
- HashMap with arrays (fast lookups)
- No need for complex graph database
- Keep it simple and fast

### 10. Token Budget Strategy
**Context sent to LLM should be ~6-10k tokens:**

Priority order:
1. Git diff (must have) - ~2k tokens
2. Changed files (must have) - ~3k tokens
3. Call graph (critical) - ~1k tokens
4. Similar patterns (nice to have) - ~1k tokens
5. Duplicate evidence (nice to have) - ~500 tokens

**Total: ~7.5k tokens** - fits in any model's context

### 11. Configuration

**Simple `.reviewrc`:**
```json
{
  "model": {
    "name": "gemma4:26b",
    "temperature": 0.2,
    "maxTokens": 128000
  },
  "review": {
    "baseBranch": "main",
    "outputPath": "./REVIEW.md"
  }
}
```

### 12. Future Enhancements (Not Now)

**Later, you mentioned:**
- Graphify integration (pre-built code graph database)
- MCP integration (Confluence/JIRA context)
- Obsidian integration (personal knowledge base)
- Chat mode (interactive reviews)
- Project planner (generate JIRA stories from requirements)
- Personal Jarvis/FRIDAY vision

**But for now:** Just get the core working - fast reviews with contract checking.

---

## What's Working (v0.2.1)
- Phase 1: Changed files ✅
- Phase 3: Pattern finding ✅
- Simple, fast reviews ✅
- 60 second completion ✅

## What's Broken (Current Attempt)
- Phase 5: Call graph hangs ❌
- Taking 15+ minutes ❌
- Something in the TypeScript parsing is slow ❌

## Next Steps (For Fresh Start)

### Approach 1: Minimal Call Graph
**Just use grep, skip AST parsing:**

```bash
# Find function definition
git diff | grep "function processPayment"

# Find all calls
grep -r "processPayment(" src/

# Present to LLM
```

Fast, simple, good enough.

### Approach 2: Lightweight AST
**Only parse changed files, not entire repo:**

1. Parse git diff to find changed functions
2. Extract their signatures
3. Use `grep` to find potential callers
4. Only parse those specific caller files to verify

### Approach 3: Skip Call Graph for Now
**Get v0.2.1 quality reviews first:**

1. Use v0.2.1 as base (works, fast)
2. Just improve the prompt
3. Add call graph later once reviews are working

---

## The Golden Rule

**"If it takes more than 2 minutes, something is fundamentally wrong."**

Don't try to fix slow code. Find the bottleneck and eliminate it completely.

---

## Your Exact Words (Key Quotes)

> "the key insight to make this work is that we dont just check if the function was modified, we also check if the signature was modified"

> "all that has to be in pre-processing and done before the llm even starts its job is to read only the relevant code"

> "we can use the abstract syntax tree module in python to generate which all dependancy is there on changed functions"

> "you can now build a packet for the llm that has git diff plus a small prompt for how to format output and then the important files that are important based on what changed and what is being called"

> "it should not take this long at all"

---

**Summary:**
- Pre-process everything (git diff → find functions → build call graph → package)
- LLM just reads and validates (no searching!)
- Target: 60-90 seconds max
- Focus: Contract mismatch detection
- Format: Structured BLOCKER/SHOULD FIX output
