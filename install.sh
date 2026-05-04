#!/bin/bash
# Installation script for MR Review Agent

set -e

INSTALL_DIR="$HOME/.mr-review-agent"
TOOL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "MR Review Agent - Installation"
echo "=========================================="
echo ""

# Create installation directory
echo "📦 Creating installation directory..."
mkdir -p "$INSTALL_DIR"

# Copy files
echo "📋 Copying agent files..."
cp -r "$TOOL_DIR"/* "$INSTALL_DIR/"

# Create virtual environment
echo "🐍 Setting up Python virtual environment..."
cd "$INSTALL_DIR"
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q tree-sitter tree-sitter-typescript gitpython ollama typer rich pydantic

# Add alias to shell config
echo "🔗 Creating 'mr-review' command..."

# Detect shell
SHELL_CONFIG=""
if [ -n "$ZSH_VERSION" ]; then
    SHELL_CONFIG="$HOME/.zshrc"
elif [ -n "$BASH_VERSION" ]; then
    SHELL_CONFIG="$HOME/.bashrc"
else
    # Try to detect from $SHELL
    case "$SHELL" in
        */zsh) SHELL_CONFIG="$HOME/.zshrc" ;;
        */bash) SHELL_CONFIG="$HOME/.bashrc" ;;
        *) SHELL_CONFIG="$HOME/.profile" ;;
    esac
fi

# Check if alias already exists
if grep -q "alias mr-review=" "$SHELL_CONFIG" 2>/dev/null; then
    echo "   'mr-review' alias already exists in $SHELL_CONFIG"
else
    echo "" >> "$SHELL_CONFIG"
    echo "# MR Review Agent (auto-added by installer)" >> "$SHELL_CONFIG"
    cat >> "$SHELL_CONFIG" << 'ALIASEOF'
alias mr-review='function _mr_review() {
  AGENT_DIR="$HOME/.mr-review-agent"
  cd "$AGENT_DIR" && source .venv/bin/activate && python cli.py review "$@";
}; _mr_review'
ALIASEOF
    echo "   ✅ Added 'mr-review' alias to $SHELL_CONFIG"
fi

echo ""
echo "=========================================="
echo "✅ Installation Complete!"
echo "=========================================="
echo ""
echo "⚠️  IMPORTANT: Reload your shell to use 'mr-review'"
echo ""
echo "Run this command:"
echo "  source $SHELL_CONFIG"
echo ""
echo "Then you can use:"
echo "  cd /path/to/your/typescript/repo"
echo "  mr-review                    # Review current branch vs main"
echo "  mr-review --base develop     # Review against develop"
echo "  mr-review --help             # Show all options"
echo ""
echo "Test installation:"
echo "  mr-review test-ollama"
echo ""
