"""Review generation skill - use Ollama to generate review."""

import ollama
from core.models import ContextPacket, ReviewReport


REVIEW_PROMPT_TEMPLATE = """You are a senior code reviewer analyzing a Merge Request. Use the provided context to generate a thorough, thoughtful review.

CRITICAL RULES:
1. Reference functions by NAME and FILE, never by line numbers
2. Signature changes with BLOCKER risk MUST be flagged - verify all callers match new signature
3. Identify duplicate interfaces and unnecessary code duplication
4. Check for code quality issues: unnecessary comments, unclean code, deep nesting, long functions
5. Look for better or simpler implementations
6. Validate that imports are correct and unused imports are removed

{context}

---

Generate a code review report in this EXACT format:

# Code Review Report

## What This MR Does
[3-5 sentences explaining the changes and their purpose]

## Current Issues

### BLOCKER (must fix):
[List any blocking issues here. For each:
**[Issue Title]** in `function_name()` at `file_path`
❌ Current: [problematic code or pattern]
✅ Fix: [suggested correction]
**Impact:** [Why this is critical]

If none, write "None"]

### SHOULD FIX:
[List issues that should be fixed but aren't blocking. For each:
- **[Issue]** in `function_name()` at `file_path`: [description]

If none, write "None"]

## Future Concerns
[Any technical debt, scalability concerns, or risks introduced by these changes]

## Code Quality
[Observations about DRY violations, clean code principles, unnecessary comments, code patterns]

## What Was Done Well
[Positive feedback - what the developer did right]

## Comments Summary
- Must fix: [number] items
- Should fix: [number] items
- Consider: [number] items

## Final Decision
**Status:** [APPROVED or COMMENTS_TO_ADDRESS]
**Files:** {files_count} | **Risk:** [LOW/MEDIUM/HIGH]
**Reason:** [One sentence explaining the decision]

---

Be specific, reference actual function names and files, and provide actionable feedback."""


class ReviewGenerator:
    """Generate code review using Ollama."""

    def __init__(self, model: str = "gemma4:26b", temperature: float = 0.2):
        self.model = model
        self.temperature = temperature

    def generate_review(self, context: ContextPacket, context_markdown: str) -> str:
        """
        Generate review using Ollama.

        Returns the raw markdown review.
        """
        # Build prompt
        prompt = REVIEW_PROMPT_TEMPLATE.format(
            context=context_markdown,
            files_count=len(context.changed_files)
        )

        try:
            # Call Ollama
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                options={
                    'temperature': self.temperature,
                    'num_predict': 4096,  # Max tokens
                }
            )

            return response['response']

        except Exception as e:
            return f"Error generating review: {str(e)}\n\nPlease ensure Ollama is running and model '{self.model}' is available."


def generate_review(
    context: ContextPacket,
    context_markdown: str,
    model: str = "gemma4:26b"
) -> str:
    """Generate code review using Ollama."""
    generator = ReviewGenerator(model=model)
    return generator.generate_review(context, context_markdown)
