# MR Review Agent 🤖

Local AI-powered Merge Request review agent using Ollama and tree-sitter.

## Features

✅ **Fast** - 60-90 second reviews for typical MRs
✅ **Local** - Uses Ollama (no cloud APIs)
✅ **Smart** - Graph-based analysis prevents hallucination
✅ **Thorough** - Catches signature changes, duplicates, code quality issues

## What It Checks

- **BLOCKER Issues**
  - Function signature changes without updating callers
  - Type mismatches
  - Breaking contract changes

- **Code Quality**
  - Duplicate interfaces
  - Duplicate code blocks
  - Unnecessary comments
  - Unclean code patterns
  - Deep nesting
  - Long functions

- **Architecture**
  - Missing test coverage
  - Better implementation suggestions
  - Technical debt

## Installation

### Prerequisites

1. **Python 3.11+**
2. **Ollama** (running locally)
   ```bash
   # Install Ollama
   curl -fsSL https://ollama.com/install.sh | sh

   # Pull model (default: gemma4:26b - ~17GB)
   ollama pull gemma4:26b

   # Or use smaller/faster models if needed:
   # ollama pull gemma2:9b    # ~5GB, faster but less accurate
   # ollama pull gemma2:2b    # ~1.6GB, very fast

   # Start server
   ollama serve
   ```

   **Model info:** https://ollama.com/library/gemma4

### Quick Install (Recommended)

```bash
# Clone repository
git clone https://github.com/RAG-KR/Python_MR_agent.git
cd Python_MR_agent

# Run installer
chmod +x install.sh
./install.sh

# Reload shell
source ~/.zshrc  # or ~/.bashrc

# Test it works
mr-review --help
```

The installer:
- Copies files to `~/.mr-review-agent/`
- Creates Python virtual environment
- Installs all dependencies from `requirements.txt`
- Adds global `mr-review` command

### Manual Install (Development)

```bash
# Clone/navigate to repo
cd Python_MR_agent

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Make CLI executable
chmod +x cli.py
```

## Usage

### Using Global Command (After install.sh)

```bash
# Navigate to any TypeScript/JavaScript repo
cd /path/to/your/repo

# Review current branch against main
mr-review

# Specify base branch
mr-review --base develop

# Use different model
mr-review --model gemma4:26b

# Custom output path
mr-review --output ./my-review.md
```

### Using Direct Python (Development)

```bash
# Review current branch against main
python cli.py review

# Specify base branch
python cli.py review --base develop

# Use different model
python cli.py review --model gemma4:26b

# Custom output path
python cli.py review --output ./my-review.md
```

### Other Commands

```bash
# Test Ollama connection
mr-review test-ollama
# or: python cli.py test-ollama

# Initialize config file
mr-review init
# or: python cli.py init

# Show help
mr-review --help
```

## How It Works

### Phase 1: Pre-Processing (40-50 seconds)

1. **Parse Git Diff** - Extract changed TypeScript/JavaScript files
2. **AST Parsing** - Use tree-sitter to extract functions, interfaces, signatures
3. **Signature Tracking** - Detect function signature changes
4. **Call Graph Building** - Find who calls changed functions (using grep + AST)
5. **Duplicate Detection** - Find similar interfaces and code blocks
6. **Context Packaging** - Format everything for LLM

### Phase 2: LLM Review (30-40 seconds)

7. **Generate Review** - Send context to Ollama (gemma4:26b)
8. **Write Report** - Save formatted markdown review

**Total Time: 70-90 seconds** ⚡

## Architecture

```
mr-review-agent/
├── skills/           # Modular capabilities
│   ├── git_parser.py
│   ├── ast_parser.py
│   ├── signature_tracker.py
│   ├── graph_builder.py
│   ├── duplicate_detector.py
│   ├── context_packager.py
│   └── review_generator.py
├── core/
│   ├── models.py     # Data structures
│   └── orchestrator.py
└── cli.py            # CLI interface
```

### Key Design Decisions

1. **No line numbers** - Uses function names + hashes for stable identification
2. **Lightweight graph** - Only analyzes changed functions, not entire repo
3. **Modular skills** - Each capability is independent and testable
4. **Pre-processing first** - All analysis done before LLM sees anything

## Configuration

Create `.reviewrc` in your repo (optional):

```json
{
  "model": {
    "name": "gemma4:26b",
    "temperature": 0.2
  },
  "review": {
    "base_branch": "main",
    "output_path": "./REVIEW.md"
  },
  "duplicate_detection": {
    "similarity_threshold": 0.85
  }
}
```

## Example Output

```markdown
# Code Review Report

**Branch**: `feature/payment-refactor`
**Files**: 3 | **Risk**: MEDIUM

## What This MR Does
This MR refactors the payment processing logic to support multiple currencies...

## Current Issues

### BLOCKER (must fix):
**Function signature changed without updating callers** in `processPayment()` at `payment.service.ts`
❌ Current: 3 callers still use old signature
✅ Fix: Update all callers to include currency parameter
**Impact:** Will cause runtime errors

### SHOULD FIX:
- **Duplicate interface** in `UserRequest`: Consider reusing existing `UserPayload`

## Code Quality
- Removed unnecessary comments (good!)
- Function complexity reduced from 15 to 8 (excellent!)

## What Was Done Well
- Comprehensive test coverage added
- Clear separation of concerns

## Final Decision
**Status:** COMMENTS_TO_ADDRESS
**Reason:** One BLOCKER issue must be resolved before merge
```

## Future Enhancements

- [ ] MCP integration (Confluence/JIRA context)
- [ ] Graphify integration (pre-built code graph)
- [ ] Chat mode (interactive reviews)
- [ ] Project planner skill
- [ ] Obsidian integration
- [ ] Multiple language support (Go, Rust, Java)

## Performance

Target performance (10-file MR):
- Git parsing: 2-5s
- AST parsing: 10-15s
- Call graph: 15-20s
- Duplicate detection: 5-10s
- Context packaging: 2-3s
- LLM generation: 30-40s

**Total: 64-93 seconds** ✅

## Troubleshooting

### "mr-review: command not found"
```bash
# Reload your shell
source ~/.zshrc  # or ~/.bashrc

# Or run installer again
./install.sh
```

### "Ollama connection failed"
```bash
# Start Ollama
ollama serve

# Verify model is available
ollama list

# Pull model if missing
ollama pull gemma4:26b
```

### "No changed files found"
```bash
# Make sure you're on a branch (not main)
git branch

# Verify there are changes
git diff main
```

### Slow reviews (>2 minutes)
- Check if ripgrep is installed: `brew install ripgrep`
- Reduce number of changed files
- Use a faster model: `gemma2:9b`

### Large MR Issues (>100 functions)
For known limitations with large MRs, see [KNOWN_ISSUES.md](KNOWN_ISSUES.md)

## License

MIT

## Credits

Built with:
- [tree-sitter](https://tree-sitter.github.io/) - Fast AST parsing
- [Ollama](https://ollama.com/) - Local LLM inference
- [GitPython](https://gitpython.readthedocs.io/) - Git integration
- [Typer](https://typer.tiangolo.com/) - CLI framework
